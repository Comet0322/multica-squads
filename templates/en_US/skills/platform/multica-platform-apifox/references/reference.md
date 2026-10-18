# Apifox Case Supplement - Reference Manual

**Fixed base URL**: `https://apifox.example.com`

---

## Common errors

| Symptom | Cause | Action |
|------|------|------|
| MCP 403 / project get 403 | No project permission or wrong ID | Use a token of an account with permission, or re-check the project ID; **never** automatically switch to another project and continue |
| MCP/CLI 401 | Invalid token | `apifox auth login --api-base-url https://apifox.example.com` |
| MCP 403 | No project permission | Use a token of an account with permission; never switch projects and force a write |
| Connected to app.apifox.com | Wrong base URL | Use the private deployment address |
| TLS error | Self-signed certificate | Prefer configuring the enterprise CA; if impossible, explicitly set `APIFOX_INSECURE_TLS=1` |
| Automation caller branch required | Cannot write directly to main | Use an AI branch |
| create Invalid Parameter | Endpoint not picked | `branch pick-to --endpoint-ids` |
| merge 422001 | AI write not enabled on main | Merge in the client |
| path is null | Partial update | Use `safe-update-case.js` |
| "This response has been deleted" (Apifox UI message) | `responseId: ""` | Use `responseId: 0` + `responseValidate: false` |
| Still validates against the success 200 | Only options were changed; the success ID is still bound | Negative cases must use `responseId: 0` |
| Endpoint/project not found | Ambiguous name, no projectId given, or non-unique match | **Stop generating**; guide the user to supply the **numeric project ID** / endpoint ID / path; upsert once the project ID is obtained; **never** invent one or force a write into the wrong project |
| Environment does not match | Used an environment from another project or a mismatching one | Check with `environment list` in the **currently confirmed project**; if there are several candidates or none, ask the user for the env ID; it may be written to the registry after confirmation; never probe against a makeshift environment |
| Asked for the project ID again for a system already seen | Registry not consulted | At task start run `systems-registry.js lookup --name <system-name>` first; on a hit still re-check with `project get` |
| Treated a few example projects in the instructions as the full set | Hard-coded project list | **Forbidden**; there are many projects, only trust user input / registry / unique match by name |
| Multiple scenarios created for one endpoint | "Expand the scenario" was understood as creating multiple scenarios | **One endpoint belongs to one scenario**; cover with differentiated steps inside the scenario; delete and converge mistakenly created ones |
| Assertion failure: root object include number | `responseJson` path=`$.` + include `"1001001"` | Use `responseText include`, or point the JSONPath at a field/array |
| Brittle whole-body equal snapshot fails | Whole-body snapshot of a list body | Switch to structural/key-field assertions and re-run with `apifox run` |

---

## System registry

Empty template: `.apifox/systems-registry.example.json`. The runtime file is resolved by `systems-registry.js` (**contains no token**).

```bash
node scripts/systems-registry.js path          # show the actual read/write path
node scripts/systems-registry.js list
node scripts/systems-registry.js lookup --name "SomeSystem"
node scripts/systems-registry.js upsert --name "SomeSystem" --project-id 123 --project-name "SomeSystem" --env-id 456 --env-name test-environment
```

Path priority: `APIFOX_SYSTEMS_REGISTRY` -> `APIFOX_SKILL_STATE_DIR` -> `<skill>/.apifox/`; if `APIFOX_OPERATOR` / `APIFOX_USER_EMAIL` is set, the file name is `systems-registry.<operator>.json` to isolate multiple people.

Legitimate sources of a project ID: given by the user this turn -> **exact** registry lookup -> unique hit of `project list` by name; otherwise stop and ask for the numeric project ID. After `project get` passes it must be upserted. **Never invent, guess or fuzzy-match; never ship a personal registry in the shared Skill distribution.**

Environment names differ per project (SIT / test environment / ...); only match exactly after listing in the current project, or ask the user.

## Probed responses and assertion templates

### Sampling suggestion (curl)

```bash
# 1) Obtain the Cookie / Token the project's way (consistent with the discovered auth)
# 2) Call the business endpoint with the Cookie
curl.exe -sk --max-time 15 -X POST "$BASE$path" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -H "Cookie: $COOKIE" --data-binary "@body.json" -D headers.txt -o body.out -w "HTTP:%{http_code}\n"
```

### Success response (example)

```json
{ "subjectId": 39, "milestoneId": 209, "fileId": 342, "fileGroupId": "...", "versionNo": 77 }
```

| Field | Level | Assertion |
|------|------|------|
| httpCode | hard | equal `200` |
| Stable business keys such as subjectId / milestoneId / fileGroupId | hard | equal the expected request value |
| Volatile keys such as fileId / versionNo | soft | exists |

### Business error (example)

```json
{
  "success": false,
  "errorCode": "31100004",
  "errorMessage": "Feature field[subjectId] can't be null",
  "data": null
}
```

| Assertion | Example |
|------|------|
| httpCode | equal `400` |
| $.success | equal `false` |
| $.errorCode | equal `31100004` or `31100005` |
| $.errorMessage | include the field name or `not found` |
| $.fileId | notExist (if applicable) |

### Response validation switch

| Case type | responseId | options.responseValidate |
|----------|------------|--------------------------|
| Positive / boundary success | ID of the endpoint's "success" response definition | true (or omitted; on by default) |
| Non-200 negative | `0` | `false` |

> This Skill **does not generate unauthenticated cases**.

---

## Scenario design and case count (no fabrication)

**Case count = the number of rows marked "needs supplementing" in the scenario evidence table**; there is no fixed upper or lower bound.

### Evidence sources (any one suffices, must be traceable)

1. Apifox endpoint definition: required fields, types, enums, descriptions, existing response/error examples  
2. Requirements/notes/errorCode conventions known in the same module  
3. **Probing the target environment** (preferred for assertions and for "is it really validated")  
4. Existing cases of the same endpoint (to compare gaps and avoid duplicates)

### Common pitfalls

| Wrong practice | Correct practice |
|----------|----------|
| Create 10 cases for every endpoint | Few parameters: 2-3 cases is fine; for complex endpoints add per branch until covered |
| Reuse the "replace subject file" example list | Use it as a structure reference only; rewrite `caseSpecs` |
| Assert "invalid xxx must fail" without testing | Probe first; if it still returns 200, treat it as a success or drop that negative case |
| Add unauthenticated cases for "complete security dimension" | This Skill explicitly does not do that |
| Omit each optional field one by one without basis | Only omit fields that are **required or that the probe shows to error** |

### `caseSpecs` and generation

`generate-cases.js` reads **only** `caseSpecs`; there is no default list. See `config.example.json` for an example (a single-endpoint sample that can be added to or trimmed).

Each entry must contain:

- `expected.statusCode`, `expected.responseValidate`
- `evidence.scenario.type/source/summary`
- `evidence.probe.environmentId/observedAt/statusCode/responseSummary`
- `sideEffect.level/testData/cleanup`

`expected.statusCode` must match the probed status code. The generator fails outright on missing evidence, mismatching environment, duplicate names or file names.

### Environment and side effects

- `targetEnvironment.type` must be `non-production`
- `write/destructive` scenarios use dedicated test data and provide executable cleanup instructions
- Probing production is forbidden by default
- For operations that cannot be cleaned up safely, ask the user first; never run them on the grounds of "complete coverage"

---

## Processor essentials

- `requestBody.data` stores a JSON string (not rawData)
- Assertions: `assertion` + `equal` + `responseJson`
- Auth: `commonScript`, with IDs from same-module discovery
- update: **never** pass `preProcessors` alone

---

## get -> modify -> update (safe update)

```bash
node scripts/safe-update-case.js \
  --project $APIFOX_PROJECT_ID \
  --branch <AI_BRANCH> \
  --case-id 3557005 \
  --patch patch.json
```

`patch.json` example:

```json
{
  "preProcessors": [ ... ],
  "postProcessors": [ ... ],
  "responseId": 0,
  "options": { "responseValidate": false }
}
```

The script only allows `ai/` branches, forbids patches that modify `path/method/apiDetailId`, and compares these three immutable fields one by one after writing.

---

## Auth discovery CLI

```bash
set APIFOX_PROJECT_ID=<numeric ID of the current project>
set APIFOX_ENDPOINT_ID=<numeric ID of the current endpoint>
set APIFOX_SOURCE_BRANCH=main
set APIFOX_OPERATOR=<operator short name>
node scripts/discover-auth.js
# Output: auth-discovery.json (includes source, candidates, confidence, requiresConfirmation)
```

Automatic recommendation is allowed only when the step comes from the same endpoint / same module history and the script ID is verifiable in the current project. Cross-module sources, script-library keywords and leftover IDs from other projects must never be adopted automatically.
When writing into config, also record:

```json
"authDiscovery": {
  "source": "target-scenario-same-endpoint / same-endpoint / ...",
  "projectId": "<current project>",
  "moduleId": "<moduleId of the target endpoint>",
  "confidence": "high|medium|low",
  "confirmed": true,
  "validatedScripts": [{ "id": 123, "name": "real name resolved from common-script" }]
}
```

A non-`high` result must have `confirmed: true`. Script IDs in the example config are placeholders only; never copy them.

---

## AI branch policy and naming

There are two situations; **do not mix their rules**:

### A · OpenAPI sync (Backend, `sync_openapi.js`)

| Rule | Description |
| --- | --- |
| **New branch for every sync** | Every time `openapi.json` is published/changed and synced -> `branch create` a new AI branch |
| **Naming** | `ai/<ISSUE-KEY>-openapi-<YYYYMMDD>`; for several syncs on the same day `-r2`, `-r3` |
| **Forbidden** | Writing directly to `main`; reusing an old openapi branch that was already merged |
| **Details** | See [`openapi-branch-workflow.md`](openapi-branch-workflow.md) |

### B · Scenario case supplement (Tester T1 / Apifox scripts)

**Reuse the same AI branch within the same Issue by default** for `pick-to` + appending steps; create an extra one only when the user explicitly asks for a "new / multiple AI branches".

Resolution order: `APIFOX_AI_BRANCH` / config `aiBranch` -> this Issue's `ai/<ISSUE-KEY>-openapi-*` (if Backend already created it, prefer to pick from it) -> an existing unarchived working branch of the project -> if none, create once.

Naming for first creation (scenarios only, and no openapi branch yet):

```
ai/<ISSUE-KEY>-scenarios-<YYYYMMDD>
```

or the historical format: `ai/YYYYMMDD-from-main-<module-short-name>`

Later endpoints only `pick-to` + write on that branch; do not `branch create` again (except OpenAPI sync, see §A).

---

## Scenario mount (main deliverable)

Historical automation lives in the "scenario" directory tree. Supplemented cases must be imported into a scenario, not left as single-endpoint cases.

### One endpoint belongs to one scenario (mandatory)

```
Expand coverage = append differentiated steps in the same scenario
Forbidden       = creating several scenarios for the same endpoint such as "main flow / classic product / multi-language"
Exception       = the user explicitly asks to split into several scenarios; or several scenarios were agreed historically and their inputs/data-setup chains must be independent
```

When the user says "expand the scenario / supplement test scenarios", understand it as **adding steps** by default; do not create a new scenario.

### Discover the target

```bash
node scripts/discover-scenario-target.js
# recommended.folderId / scenarioId / scenarioName -> write into config.scenarioTarget
# selfHit=true -> mode must be append-existing
```

### Import steps

Preferred:

```bash
# batch-create first to get manifest.json
node scripts/append-to-scenario.js --branch <AI_BRANCH> --endpoint-id <ID> --manifest <dir>/manifest.json --apply
```

Equivalent CLI:

```bash
apifox test-scenario import-steps <SCENARIO_ID> --project $APIFOX_PROJECT_ID --branch <AI_BRANCH> \
  --source test-case --endpoint <ENDPOINT_ID> --ids <CASE_IDS> --sync manual \
  --api-base-url https://apifox.example.com
```

Rules:

1. If a historical scenario exists for the same endpoint -> append **only** to that scenario  
2. Only when the endpoint has no scenario yet, **create one** under the same-module historical `folderId`, named "`<endpoint-name>`" or "`<endpoint-name>-automation-supplement`"  
3. No folder -> stop and ask the user to specify one  
4. The AI branch must `pick-to --test-scenario-ids` or `--test-scenario-folder-ids`  
5. If the scenario already binds the same test-case / an equivalent step -> skip  
6. Mistakenly created extra scenarios of the same endpoint should be deleted and their steps converged into the single scenario (unless the user asks to keep them)  

### Assertion anti-patterns (WS-40)

| Wrong practice | Correct practice |
|----------|----------|
| Whole-body `responseJson equal` on a full list body | Structural assertions: `code`, `isNotEmpty`/`exists`, key business fields |
| `responseJson` + path=`$.` + `include` + `"1001001"` | Use `responseText include`, or point the JSONPath at an array/field and then assert |
| JSONPath filter result is an array but `equal` is used with a scalar | Use `include`, or take an index / change the path; trust the `apifox run` probe |
| Repeatedly appending near-identical assertion steps in one scenario | skip / merge; one step per differentiated dimension is enough |

---

## Idempotency and naming

- Single endpoint: `test-case list --endpoint`; if the name already exists -> skip  
- Scenario: a step bound to the same caseId already exists -> skip  
- Prefix: `APIFOX_CASE_NAME_PREFIX` or the endpoint name  

---

## Manual merge by the user

1. Switch to the AI branch and review whether the scenario steps sit in the same directory as the historical ones  
2. Merge into main  
3. **You must tick the scenarios** (`--test-scenario-ids`)  
4. Also tick the corresponding `--test-case-ids` (recommended)  
5. **Do not** tick only single-endpoint test cases (they would be separated from the historical scenario tree)  
6. **Do not** tick endpoint / response definitions  
7. CLI example (only when the user explicitly asks):

```bash
apifox branch merge --project $APIFOX_PROJECT_ID --type ai \
  --from <AI_BRANCH> --to main \
  --test-scenario-ids <SCENARIO_ID> \
  --test-case-ids <CASE_IDS>
```

---

## MCP mcp.json (Windows)

```json
{
  "mcpServers": {
    "apifox": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "apifox-mcp-server@latest", "--project-id=YOUR_PROJECT_ID"],
      "env": {
        "APIFOX_ACCESS_TOKEN": "YOUR_TOKEN",
        "APIFOX_API_BASE_URL": "https://apifox.example.com",
        "NODE_EXTRA_CA_CERTS": "C:\\path\\to\\company-ca.pem"
      }
    }
  }
}
```

On the script side, use `APIFOX_INSECURE_TLS=1` only when the enterprise CA cannot be configured; it explicitly disables TLS verification and prints a warning. Put the token only in environment variables or a credential store, never in `config.json`.
