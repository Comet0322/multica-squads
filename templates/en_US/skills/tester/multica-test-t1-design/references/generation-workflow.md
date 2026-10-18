# T1 Generation Workflow (mandatory rules)

> Consolidated from `test-case-generator-squad` SKILL v3.5. Use together with [`design-trace.md`](design-trace.md), [`test-case-template.md`](test-case-template.md) and [`coverage-checklist.md`](coverage-checklist.md).

## Three-phase delivery (Confluence master copy -> human review -> XMind/JIRA)

### Phase A: Confluence maintenance (T1/T2 end here by default)

1. Generate the functional-case JSON (working file; optionally keep `docs/test/<KEY>/test_cases.json`)
2. API cases only as local `test_cases_api.json` (not imported to JIRA)
3. Write the **full case body** into `t1-cases.md` (not a summary) and publish it as a child page of the Confluence Issue Hub
4. T2 likewise: `t2-coverage.md` is published to Confluence incrementally
5. In parallel: once the API contract is ready -> `multica-platform-apifox` supplements scenarios (AI branch)
6. **Do not generate XMind**; output the coverage report + **pending-review note**, then **stop**

**Phase A closing statement (mandatory):**

```text
Status: pending human review (Confluence updated, XMind not generated / not imported to JIRA)
Confluence: <t1-cases or t2-coverage URL>
Example passphrase to confirm import: "Review approved, import to JIRA"
```

### Phase B: Human review

- `multica-review-test`: Block / Revise / Pass (reviews the Confluence body, not XMind)
- Humans edit on Confluence -> Tester updates the local md -> republish
- Review Pass **is not** import authorization

### Phase C: XMind + JIRA (only after an explicit 👤 passphrase)

After the user approves the review and explicitly gives the import instruction, you **must**, in order:

1. Sync from the latest Confluence/JSON -> `generate_xmind.py` -> `test_cases_{JIRA_KEY}.xmind`
2. `import_to_tracker.py` (functional cases only; unique `--suite-name`)
3. Story <-> case-set Task: **JIRA Relates** (no Include fan-out of cases)
4. Update the Confluence status to "Imported to JIRA" + case-set link

```text
Requirement (Story)  --[JIRA Relates]-->  Test case set (Task)
Test case            --[test-management platform case tree]--> Test case set
Test case            --[test-management platform requirement panel]--> Test case set (Task)   <- not the Story
```

| Prohibited | Reason |
| --- | --- |
| Generating XMind in T1/T2 Phase A | The master copy is on Confluence; avoid dual sources |
| Importing without review | Cases not confirmed |
| Creating Include from case set -> cases | Issue links fan out all cases |
| Attaching cases to the Story in the requirement panel | The Story page's test panel fans out |
| Importing API cases | API cases go through Apifox + manifest |

### Explicit import passphrase (any one is required for Phase C)

- "Review approved, import to JIRA"
- "Import to JIRA" / "import jira"
- "Continue import" / "Confirm import" / "OK to import"
- "Import under test-suite name XX"

Vague phrasing ("looks fine", "let me look again") -> **do not** import; ask a follow-up.

> Even if the user writes "generate and import" in the task card, Phase A (publish to Confluence) must still be completed first; **do not** skip review or generate XMind in the same turn.

### Phase C CLI (XMind -> JIRA)

**Generate XMind first** (functional cases only):

```bash
python scripts/generate_xmind.py \
  --input ./data/test_cases.json \
  --output ./data/test_cases_{JIRA_KEY}.xmind
```

**File name**: `test_cases_{JIRA_KEY}.xmind`; **do not delete xmind files of other Keys**.

### Import CLI (correct parameters)

```bash
python scripts/import_to_tracker.py \
  --jira-url "https://your-domain.atlassian.net/browse/PROJ-123" \
  --input ./data/test_cases.json \
  --suite-name "Order Status Tags and Filters"
```

Optional: `--dry-run` to preview, `--manual` to confirm one by one, `--update-existing` to update descriptions of existing cases.

### High risk: no duplicate imports

Each batch of cases is **imported only once** and filed into **one** test-management-platform case set.

Prohibited:

- Importing the same batch into multiple test-management-platform case sets
- Running the import script repeatedly (e.g. dry-run and then two real imports)
- Importing manually first and then re-linking by script (duplicate linking)

**Pre-import validation (required):**

1. Confirm this JIRA Key (e.g. PROJ-123) is the link target
2. Confirm test cases under this requirement have not been imported yet (check in JIRA whether test sub-tasks already exist)
3. Confirm `--suite-name` is **unique**
4. Confirm the suite name strictly corresponds to the current requirement and does not duplicate or resemble an existing suite

**If already imported:** do not import again; report the existing case info directly.

### Test case set naming rules

**`--suite-name` must be specified manually; do not rely on auto-derivation.**

1. **Read the requirement title** — the JIRA summary
2. **Strip meaningless prefixes** — `[Backend]`, `[Module B]`, `[Optimization]`, `[Bug]`, etc.
3. **Extract the core business meaning** — concise and professional (a short phrase)
4. **Do not make things up** — strictly based on the requirement content
5. **Pass explicitly** — as `--suite-name`
6. **Check uniqueness** — it does not exist in the test-management-platform case-set list, or it is confirmed to be the old set for the same requirement

| JIRA requirement title | Distilled suite name |
| --- | --- |
| [Backend] Order export - quick download of receiving records | Order export receiving records quick download |
| [Module B] Order detail page - new data display | Order detail page new data display |
| Login page UI refactor | Login page UI refactor |
| [Optimization] User management - bulk import optimization | User management - bulk import |
| [Bug] Order list query is slow | Order list query performance |

**Fallback rule:** when the title is not enough to distill -> `{system prefix}-functional cases`.

### Post-import link validation (required)

After import, self-check against live examples (see PROJ-124 / PROJ-125):

1. **Story issue links**: only Relates to the test case set Task; do not list all cases directly
2. **Test case set issue links**: only Relates to the Story; **must not** Include each case in bulk
3. **Single case**: already in the test-management-platform case tree; the platform's "Requirement" panel points to the **case set Task**, not the Story
4. If Include links exist or the requirement panel points to the Story: fix per the rules, and confirm `import_to_tracker.py` has not regressed to the old logic

---

## Step 0.5 Historical context (Confluence + knowledge base)

### Step 0.5a — Confluence history search

Search Confluence with requirement keywords for past requirements/designs/API docs as **background reference** (the current JIRA still governs). Write hits into the "Historical context reference" section of the coverage report.

### Step 0.5b — Team knowledge base (two-way usage split)

Call the team knowledge-base Q&A script (optional; no SSH/curl). See the team knowledge-base onboarding doc for rules.

| Information type | May enter cases | Where to write |
| --- | --- | --- |
| Menu paths, page entry points, permission names, text aliases | **Should be used** | `preconditions` / `steps` / `module` |
| Historical rules, other systems' conventions, fields the current requirement does not mention | **Must not be treated as acceptance points** | Background only; `expected_results` still follow the current AC |

**Three knowledge-base questions (follow-ups must cover at least these; do not only ask for rule keywords):**

1. What is the module's **entry/menu path**?
2. What is the **operation flow** of the related pages (tabs, buttons, wait points)?
3. What is the **permission convention** (role/capability names)?

You may pass the system code by JIRA prefix to narrow scope (business-system codes such as `CRM`, `MES`).

```bash
python scripts/kb_ask.py (team KB Q&A script, optional) --health
python scripts/kb_ask.py (team KB Q&A script, optional) "[Module name] entry and operation path" <system-code>
python scripts/kb_ask.py (team KB Q&A script, optional) "[Module name] permissions and role requirements" <system-code>
```

### Step 0.5 execution flow

1. **Extract keywords** — pull 2–5 core business terms from the JIRA title/description/AC (system code, module name, feature name, entity, operation type)
2. **Confluence history** — search past requirements/designs/APIs/test docs with the keywords
3. **Team knowledge base** — same keywords + the three questions; ask after `--health` passes
4. **Persist in two buckets** — the **operation bucket** (path/permission/text) goes into steps; the **rule bucket** (historical rules/old fields) is for understanding only
5. **Record information sources** — in the "Historical context reference" of the coverage report: Confluence titles/links + knowledge-base summary and citations (as returned by the script; never fabricate)

### Step 0.5 mandatory constraints (shared by Confluence and the knowledge base)

- **Rules are not acceptance; operations must go into steps** — historical/KB rules must not be treated as AC; entry/permission/text within the current requirement scope **must** be written into steps
- **Strictly limited to the current requirement scope** — do not generate test points the current JIRA does not mention
- **No speculation** — if neither the reference source nor the current requirement says it -> it must not be a test basis; menu paths follow reference source + current state; never invent menus
- **No divergence** — do not extend the whole historical module scope into this batch of cases
- **Conflict priority** — JIRA AC > current Confluence PRD > API > Figma > history/knowledge base

### Step 0.5 scenario examples

| Scenario | Correct approach | Wrong approach |
| --- | --- | --- |
| Add "bulk import" | Check Confluence + KB to learn the template format and help design boundary cases **within the current requirement scope** | Treat historical "import fields A/B/C" directly as current test points |
| Modify "approval flow" | Use historical nodes to help with exception scenarios; steps/expectations still follow the **current requirement's nodes** | Copy historical approval cases and ignore that nodes have changed |
| Add a query page | Use entity field meanings to help think about filter combinations | Write cases using historical old fields as the current page's fields |
| KB has a full CRM module description, but the current change is one text edit | Generate only text-change cases; KB is used just to avoid misreading terms | Expand to the whole module because the KB is rich |

Knowledge base unavailable: mark "knowledge base unavailable" in the coverage report, **do not block** generation; never invent rules. For timeout stop-the-round handling see the team knowledge-base onboarding doc.

---

## Steps and expected results (5 principles)

1. **Atomic merge**: an action plus its immediate verification may be merged into one step (e.g. "click the tab and confirm the list refreshes")
2. **Complete expectation set**: within one step, number with `1)` `2)`, with a blank line between numbers
3. **Unlimited verification points**: within one step, list multiple verification points by number; but at the JSON array level `steps`/`expected_results` must still be **1:1 and equal length** (see [`output-format.md`](output-format.md))
4. **Consistent templates for the same kind**: same-type operations (e.g. chart checks) have the same expectation structure
5. **No empty expectations**: if there is no expectation, re-examine whether the step is needed

**Expected-result quality (non-negotiable):**

- Map step by step; scripts must not auto-fill missing expectations
- Precisely match the step's **immediate feedback**; do not jump to the final state
- Concise language; no vague words such as "should" or "may"
- Unparsed wiki markup must not enter case bodies

**Prohibited**: `{LQ}` `{RQ}` `[TBD]` `[Figma missing]`, literal `XXX` permission placeholders, hard-coded accounts/passwords.

---

## Module hierarchy and priority

**module path**: separated by `/`; the JSON `module` matches the XMind/JIRA tree structure.

### XMind / module hierarchy spec

| Level | Meaning | Rule |
| --- | --- | --- |
| Level 1 (root) | System name | Issue Key prefix: e.g. `PROJ`; **do not default to another project's prefix** |
| Level 2 | Requirement name | e.g. "Order export receiving records quick download" |
| Level 3 | Business-domain root module | Extracted from the requirement content (e.g. "Order Center", "CRM"); no guessing, no omission |
| Level 4 | Module name | With a prefix when there are multiple business domains (e.g. `CRM-Order Export`); a single domain may use the module name directly |
| Level 5+ | Sub-module | Keep splitting by business logic; cases hang under the last sub-module |

**Example hierarchies:**

```text
Multiple domains:   CRM > Order Export Phase 2 > Order > Receiving Record Download > concrete case
Single domain:      CRM > Order Export Phase 2 > Receiving Record Download > concrete case
With sub-module:    CRM > Order Export Phase 2 > Receiving Record Download > Download Format Config > concrete case
With domain root:   Order Center > Order Detail > New Data Display > Data Display Config > concrete case
```

**module JSON example:** `Order Detail/New Data Display/Data Display Config` (flat names such as `New Data Display-Data Display Config` are prohibited)

```text
{system prefix} > {requirement name} > {business-domain root} > {module} > [sub-module…]
```

**priority** (P0 prohibited):

| Level | Scenario |
| --- | --- |
| P1 | Core main acceptance path |
| P2 | Normal/auxiliary/page checks |
| P3 | Exceptions, boundaries, permission denial |

Rule: exception/boundary -> P3; core main path -> P1; the rest -> P2.

---

## Executability (system-wide mandatory)

See [`executability-and-permissions.md`](executability-and-permissions.md) (two goals, **permission identification order**, module naming, KB self-check, post-generation checklist).

Summary:

1. **Two goals**: executable (real entry path) + traceable (maps to AC)
2. **Permission template**: `Log in with an account that has the {system} [{module/operation}] permission` (fill in the real permission name, not XXX)
3. **Actionable steps**: spell out paths such as System -> Module -> Feature; wait for loading; test-data aliases
4. **Knowledge-base operation bucket goes into steps**; the rule bucket does not go into expected

### Auto-dedup during generation

Avoid duplicate cases during generation (same module, same scenario, same operation path generated once); no need to compare against existing Jira cases. The import stage `import_to_tracker.py` additionally dedups on the JIRA side.

### Merge and split strategy

- **Mergeable**: equivalent negative cases with the same entry and same verification technique (e.g. Count=0 / <=1mm / =1.0mm) can be merged into one, listing each sample by number in the expected result
- **Keep standalone**: key boundaries whose failure cannot be root-caused after merging, or standalone PRD risk items (e.g. consistency between detail and filter) keep their own case

Post-generation self-check: see [`coverage-checklist.md`](coverage-checklist.md) + this section's quality checklist:

- [ ] No hard-coded accounts/passwords; no XXX placeholders
- [ ] Steps contain a real entry point or backend trigger
- [ ] Core AC traceable; anything uncovered is written as uncovered
- [ ] Priority P1/P2/P3 correct; no P0
- [ ] module matches product navigation

---

## Figma and API docs (handling missing resources)

Before generation, scan the JIRA comments/description/attachments for Figma links. See [`web-ui-checkpoints.md`](web-ui-checkpoints.md).

**When Figma is missing (mandatory):**

1. First look for Figma in JIRA per the rules and try to fetch it
2. Design found -> write precise expectations based on the design
3. Not found but the step allows a clear expectation to be derived (e.g. "Cancel" -> dialog closes) -> write the clear expectation directly
4. Expectation **must depend on** Figma (color/position/interaction details) -> report a blocker **before** generation

**Do not** use placeholders such as `[Figma missing…]` in cases.

**When the API doc is missing:** placeholders are likewise prohibited; if the request/response structure cannot be determined -> report a blocker before generation.

---

## JSON and coverage self-check table

For the full JSON schema, the six Output Delivery rules, and the **coverage self-check table** format, see [`output-format.md`](output-format.md) (**mandatory** in Phase A).

## Coverage report template (must be attached in Phase A)

```markdown
# Test Case Coverage Report — {JIRA_KEY}

## Status
Pending human review (not imported to JIRA)

## Design traceability
(see the design-trace table summary)

## Module coverage matrix
| Module | Full | Boundary | Page check | Case count |
| --- | --- | --- | --- | --- |

## AC coverage
| AC-/rule | Corresponding cases | Status |
| --- | --- | --- |

## Knowledge base / history
- Knowledge base: available/unavailable; whether the operation bucket was written into steps
- Confluence history: cited titles

## Artifacts
- JSON: {path}
- XMind: test_cases_{KEY}.xmind
- API JSON (if any): test_cases_api.json (not imported to JIRA)

## Blockers / uncovered
- …
```

---

## API cases (local only)

- Output `test_cases_api.json`; **never** import into JIRA / XMind / test-management platform
- Executable scenarios -> `multica-platform-apifox`

For dimension selection and coverage matrix see [`coverage-dimensions.md`](coverage-dimensions.md). (T1 in parallel)
- See [`api-testing-guide.md`](api-testing-guide.md)
