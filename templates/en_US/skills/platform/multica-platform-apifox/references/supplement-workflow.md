# Apifox Endpoint Scenario Supplement Workflow

> Consolidated from `apifox-test-case-supplement-squad`. Use together with [`reference.md`](reference.md) and [`agent-instructions.md`](agent-instructions.md).

## Applicable stages

- **T1 in parallel** (alongside the API contract and functional case generation)
- **T2**: supplement endpoint scenarios against the contract diff
- **Does not own T3 batch runs** (T3 -> `scripts/run_apifox.py` / `multica-test-t3-api-automation`)

## Task card (stop if anything is missing)

```text
System name:
projectId:            # numeric; if absent, registry lookup, otherwise stop and ask
environmentId/name:
Endpoint:             # ID or METHOD + path
Write intent:         # supplement directly | review first, then write
Operator:             # APIFOX_OPERATOR
```

## Project registry

```bash
node scripts/systems-registry.js path
node scripts/systems-registry.js lookup --name "<system-name>"
node scripts/systems-registry.js upsert --name "<system-name>" --project-id <ID> ...
```

Registry file: `.apifox/systems-registry.example.json` -> copy it to an operator-isolated `systems-registry.json` (never commit a token).

**Registry path resolution (in priority order):**

1. `APIFOX_SYSTEMS_REGISTRY` (full file path)
2. `APIFOX_SKILL_STATE_DIR/systems-registry[.operator].json`
3. `<skill>/.apifox/systems-registry[.operator].json`

`operator` comes from `APIFOX_OPERATOR` or `APIFOX_USER_EMAIL`.

## Custom inputs

| Input | Environment variable | Required | Description |
| --- | --- | --- | --- |
| Access Token | `APIFOX_ACCESS_TOKEN` | Yes | Environment variable / Secret only; never write it into config |
| Operator | `APIFOX_OPERATOR` / `APIFOX_USER_EMAIL` | Recommended for teams | Isolates the registry; suffix of AI branch names |
| Registry path | `APIFOX_SYSTEMS_REGISTRY` / `APIFOX_SKILL_STATE_DIR` | No | Workspace-level state directory |
| Project ID | `APIFOX_PROJECT_ID` | Yes | Numeric ID; must match the project the user means |
| Target endpoint | `APIFOX_ENDPOINT_ID` / name / path | Yes | Must be uniquely located within the **current project** |
| Environment ID | `APIFOX_ENVIRONMENT_ID` | Required for probing | Must belong to the current project and be non-production; **never default to SIT** |
| Source branch | `APIFOX_SOURCE_BRANCH` | No | Defaults to `main` |
| AI branch | `APIFOX_AI_BRANCH` / config `aiBranch` | Recommended | Reuse for the same operator; ask first across people |
| Case name prefix | `APIFOX_CASE_NAME_PREFIX` | No | Defaults to the endpoint name |
| Base request | config `baseRequest` | At generation | path/query/header/body; non-production test data |
| Case list | config `caseSpecs` | At generation | **Derived from the review/design**, not a fixed template |
| Target environment nature | config `targetEnvironment` | Required for probing | `non-production`; probing production is forbidden by default |
| Scenario mount | config `scenarioTarget` | At delivery | Folder/ID of historical scenarios in the same module |

Auth pre-processors are **not** a custom input; they must go through the "auth discovery" flow. For TLS prefer the enterprise CA; if a self-signed certificate cannot be verified, set `APIFOX_INSECURE_TLS=1`.

**Do not hard-code globally** (people would cross projects): `APIFOX_PROJECT_ID`, `APIFOX_ENVIRONMENT_ID`, `APIFOX_ENDPOINT_ID`, `APIFOX_AI_BRANCH` — resolve them from task input or the registry.

## Project / endpoint / environment binding (mandatory)

Binding validation must be complete before any review or write:

0. **Project ID** — explicit from the user -> registry lookup -> unique by name -> otherwise stop and ask; on 403 **never** switch to another project
1. **Project** — `project get` to re-check the name against what the user/registry says
2. **Endpoint** — locate by ID / exact path / exact name within the current project; 0 or several matches -> guide the user to pick one
3. **Environment** — confirm with `environment list/get` that it belongs to the current project; names differ per project, never default to SIT
4. If any step fails -> **output only guiding questions and candidates**; do not create an AI branch, write caseSpecs or Apply

### Guiding questions (short and concrete)

When the project is undetermined:

```text
Could not uniquely determine the target project (system name: "xxx"). Registry miss / lookup by name returned 0 or several candidates.
Please provide the numeric project ID (visible in the Apifox project settings).
Once provided I will validate it with project get and write it to systems-registry, so the same system can be reused next time.
```

When the endpoint is not found:

```text
Endpoint "xxx" was not found in the confirmed project "<project-name>" (<projectId>). Please fill in any one of:
1) Endpoint ID (numeric)
2) Method + full path (e.g. POST /api/...)
3) Name of the module/folder it belongs to
If the target project is wrong, give the correct project name or project ID.
```

## Deliverable principles

| Layer | Role | When merging to main |
| --- | --- | --- |
| Scenario `test-scenario` | **Main deliverable**; in the same directory tree as historical scenarios | **Must be ticked** via `--test-scenario-ids` |
| Single-endpoint case `test-case` | Source of steps, imported into the scenario via `import-steps` | Recommended to tick via `--test-case-ids` |
| Endpoint definition | Only pick, never modify | **Do not tick** |

A missing scenario mount = **not done**.

## One endpoint <-> one scenario (WS-40)

**Default model:** one endpoint (same projectId + apiDetailId) belongs to **one** scenario; expanding coverage = appending differentiated steps inside that scenario.

| What the user says | Correct understanding | Wrong understanding |
| --- | --- | --- |
| Expand/supplement test scenarios | Add steps to the **existing scenario of the same endpoint** | `test-scenario create` several more scenarios for the same endpoint |
| Merge duplicate endpoints | Remove duplicate/stale steps inside the scenario and converge on the necessary differentiated steps | Split into several scenarios to "pretend" full coverage |
| Supplement cases | A single-endpoint `test-case` is only a step source and must ultimately appear in **that one** scenario | Piling up single-endpoint cases, or creating one scenario per assertion dimension |

**Hard rules:**

1. If the target endpoint is **already in a scenario** -> `scenarioTarget.mode` **must** be `append-existing`; do not create separate scenarios for dimensions such as "classic product / multi-language / main flow"
2. If the same module's history has **no** scenario bound to the endpoint -> only then may you **create one** under the same `folderId` (e.g. `<endpoint-name>-automation-supplement`); later expansion keeps appending to it
3. Multiple scenarios are allowed only if the user explicitly says "open another scenario / split into several scenarios"; the colloquial "expand the scenario" is still executed as **adding steps**
4. If the endpoint is already in several scenarios -> by default append to the **preferred scenario**; unless the user asks to keep several, converge the mistakenly created ones
5. Steps within one scenario must be **differentiated** (different assertion dimensions or different verified inputs); appending steps with nearly identical assertions or whole-body equality snapshots is forbidden
6. A single-endpoint `test-case` may be one step per case as a source; leaving unrelated duplicate/stale cases behind is forbidden

**Assertion quality (companion to the scenario structure):**

- Assertions are based on non-production probes; re-run with `apifox run -t <scenarioId>` before delivery
- **Forbidden**: whole-body `responseJson equal` snapshots
- **Forbidden**: `include` on the `responseJson` root path `$.` with a purely numeric string value
- When a JSONPath filter returns an array, do not `equal` a scalar directly; use `include` / an index / rewrite the path

## Case count and scenario principles

**The number of cases is not limited** — no fixed N, and no padding just to "look like enough".

| Principle | Description |
| --- | --- |
| Depends on the endpoint | Few parameters, simple rules -> few cases; many parameters, many branches -> many cases |
| Scenarios must be complete | Cover the capabilities of the endpoint that are **verified**; land them as **multiple steps in one scenario**, not multiple scenarios |
| No fabrication | Every case must cite a source: endpoint definition, requirement, error code, same-module historical assertion, or probe |
| Probe when in doubt | If the docs are unclear, sample first; if the result contradicts the assumption, change the case |
| No unauthenticated cases | Do not cover "unauthenticated / not logged in" scenarios |
| Skip what is covered | If the target scenario already has an equivalent step / same name -> skip; do not open a new scenario to get around skip |

## Main flow

```
Input -> align task card -> system registry path/lookup (upsert if new system + project ID)
  -> validate project/endpoint/environment alignment (on failure guide and stop)
  -> connectivity -> review (evidence table) -> auth discovery -> scenario mount target discovery
  -> probe sampling -> design caseSpecs -> generate JSON
  -> resolve/reuse the AI branch (ask first on cross-person conflicts) -> pick (endpoint + scenario)
  -> create single-endpoint cases (idempotent) -> scenario get concurrency check -> import-steps -> self-check -> report
```

1. **Auth discovery** — `node scripts/discover-auth.js` -> `auth-discovery.json`
2. **Scenario discovery** — `node scripts/discover-scenario-target.js` -> prefer `append-existing`
3. **Generate cases** — `node scripts/generate-cases.js` (config: see `scripts/config.example.json`)
4. **Write into the scenario** — `node scripts/append-to-scenario.js` or `batch-create.ps1`
5. **Safe update** — `node scripts/safe-update-case.js` (never change path/method/apiDetailId)

## Scenario evidence table (mandatory output of the review stage)

**No evidence, no write.** Under one endpoint the "scenario name" should point to the **same** `scenarioId` (unless the user explicitly asks to split scenarios).

| Scenario name | Dimension | Evidence type | Source locator | Probe environment/time | Already exists | Supplement or not |
| --- | --- | --- | --- | --- | --- | --- |
| ... | positive/negative/boundary | endpoint definition/requirement/probe/same-module history | ... | ... | yes/no | yes/no/skip |

## Mandatory constraints (16)

1. **Only add test resources**; never add or modify endpoint path/method/parameters/response definitions/schema
2. Do not modify existing steps/cases unless the user explicitly asks
3. **Always write on an AI branch**; **never auto-merge main**
4. **Reuse the same AI branch by default**; do not create a new one on every generation (except when the user explicitly asks to "open another branch")
5. Auth pre-processors: discover from historical steps by **current project + target moduleId**; never reuse across projects/modules
6. **Assertions must be based on probed responses**; never invent them from OpenAPI alone
7. Run `cli-schema validate` before create/update; use `safe-update-case.js` for single-endpoint updates; for scenario updates, get the full structure before writing back
8. Non-200 negative cases: `responseId: 0` + `options.responseValidate: false`; positive cases bind the success `responseId`
9. Same-name policy: if the target scenario already has an equivalent step / same name -> **skip**
10. **Never** apply one endpoint's fixed list to other endpoints
11. Writes are allowed only on `ai/` branches; batch creation and scenario import must pass dry-run before Apply
12. **Write confirmation policy**: when the user's intent is "supplement directly / generate and write cases" and review + probe + dry-run have all passed, **Apply and import-steps directly in the same turn**; do not stop at "awaiting confirmation" and deliver nothing. Stop and wait only when the user explicitly asks for "review first, write later / show me the dry-run first / do not write"
13. Probing is limited to non-production; for side effects, state the test data and cleanup; if cleanup cannot be done safely, ask the user to confirm first
14. `caseSpecs.evidence`, the expected status code and the assertion basis are required
15. New system + user-provided project ID: after validation passes, `systems-registry.js upsert`; a project ID may only come from the user / registry / unique match by name, **never invented**
16. Cases **must** be imported into a scenario before reporting completion; merge guidance must include the scenario ID; project/endpoint/environment must align with the user's target

## AI branch policy

- Default: the same operator reuses the same AI branch within the same project session
- Naming (first creation only): `ai/YYYYMMDD-from-<source-branch>-<module-short-name>[-<operator>]`
- If another person's active branch is found -> **ask** whether to reuse or create a new one; never silently squeeze in
- Before writing a new endpoint, `pick-to` on the same AI branch is enough; no new branch is needed

## Scenario concurrency (multiple people)

Run `test-scenario get` once more **before** `import-steps` / scenario update:

- If the step count / key steps have been clearly changed by someone else since the review -> **stop writing**, report the differences, and continue only after the user confirms
- If someone else already created a duplicate scenario for the same endpoint -> by default attach to the preferred scenario and suggest converging; do not stack a third one

## Hard constraints (quick reference)

- Enterprise private base URL: `config.yaml` -> `api_base_url` (not the public app.apifox.com)
- **Never** patch the endpoint definition (path/method/apiDetailId)
- One endpoint belongs to **one** scenario; expansion = appending steps, never creating duplicate scenarios
- Token via environment variables only; never write it into config/Git
- **Never** generate unauthenticated scenarios

## Pre-merge self-check checklist

```
- [ ] Task card complete: system name/projectId/env/endpoint/write intent/operator
- [ ] Project ID comes from the user / exact registry lookup; re-checked with project get
- [ ] On 403/no permission, did not switch projects on my own
- [ ] Scenario evidence table produced; items without evidence were not written
- [ ] dry-run passed; if the intent was direct supplement, Apply + import-steps in the same turn (did not stop awaiting confirmation without reason)
- [ ] No multiple scenarios for one endpoint; expansion = appending steps in the same scenario
- [ ] scenario get concurrency check before import (see "Scenario concurrency")
- [ ] Auth comes from same-module historical steps; non-high confidence was manually confirmed
- [ ] Positive/negative responseId set correctly; assertions re-run with apifox run
- [ ] main not auto-merged; endpoint definition not changed
- [ ] No unauthenticated scenarios generated
- [ ] Report contains the scenario ID and merge guidance
```

For assertion quality and case-count principles see [`reference.md`](reference.md).

## The report must include

- System name, projectId, environmentId and their **sources** (user / registry / by name)
- Operator; AI branch name
- The single scenarioId / folder / scenario name
- IDs of the imported cases/steps
- Auth source (projectId + moduleId + step/case)
- Evidence table summary and key probe findings
- Merge tick guidance (**the scenario must be ticked**, the corresponding test-case is recommended)
- If the registry was upserted, state that the mapping was registered

If a self-check fails (wrong project, invented IDs, missing scenario mount, hard-coded auth, un-probed assertions, etc.), **do not** claim completion.

## Version history

See [`CHANGELOG.md`](CHANGELOG.md) (consolidated from apifox-test-case-supplement-squad).

## OpenAPI sync (Backend only)

Endpoint definition add/change/delete + Issue tagging -> `scripts/sync_openapi.js` (a separate track from scenario supplementing).
