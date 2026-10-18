---
name: multica-review-product
description: "Requirements/PRD dedicated review framework. ProductReviewer reviews the PRD submitted via multica-pm-artifact-publish in three stages (value / logic / clarity), outputs PASS/FAIL/BLOCKED with Must Fix/Suggest/Nit, and reports to Leader; after a FAIL, PM Workflow B updates the PRD and a re-review follows."
---

# Requirements (PRD) Professional Review (ProductReviewer)

This skill provides a structured professional review of **PRD / requirement artifacts**. It is called by `ProductReviewer`; the review target is the Confluence / JIRA link that `ProductManager` returns via `multica-pm-artifact-publish`.

Agent instructions: [`references/agent-instructions.md`](references/agent-instructions.md).
Execution order: [`references/review-workflow.md`](references/review-workflow.md).
Checklist: [`references/checklist.md`](references/checklist.md).
Report format: [`references/report-template.md`](references/report-template.md).

## When to use

- ProductReviewer receives a "review PRD" task dispatched by Leader.
- A **re-review** round after PM's **Workflow B update** (check the previous round's Must Fix items one by one).

## Platform collaboration (optional, read-only)

| Platform skill | Purpose |
| --- | --- |
| `Team knowledge base (optional)` | Check terminology, module boundaries, historical background (**reference only**) |
| `multica-platform-confluence` / `multica-platform-jira` | Read-only fetch of the PRD when Leader did not provide the full text (never create or change status) |

**Two ways to use the KB (consistent with the PM spec):**

- May cite: terminology, entry paths, permission-name aliases (to check whether the PRD states them clearly)
- **Forbidden**: treating KB/Confluence **historical rules** as the "expected AC/FR" of the current PRD (rule expansion is a Must Fix-level misjudgment; mark it as a reference difference, not a PM defect)
- KB unavailable: note "knowledge base unavailable", **do not BLOCK**, and keep reviewing the PRD body

## Review inputs (BLOCKED if missing)

| Required | Description |
| --- | --- |
| **Full PRD text** | Confluence/JIRA link, or equivalent body text provided by Leader |
| **Requirement context** | Issue, Story Key, business background (in Leader's dispatch or the Issue) |

| Optional | Description |
| --- | --- |
| Prototype / Figma link | Check for conflicts with the written PRD |
| Data definitions, dependent systems | For cross-system / dashboard requirements |

If both the case source and the PRD are missing -> **BLOCKED**; list the missing items and report to Leader.

## Three-stage review (strict order)

### Stage 1: Value judgment

Assess whether the requirement is worth pursuing within the current scope (write the conclusion into the report; **a fatal value flaw -> Must Fix -> FAIL**):

- Problem reality: does it solve a real, pressing business/user problem
- Value and ROI: are the benefits clear and measurable; is the input/output reasonable
- Timing and priority: should the scope be phased rather than done all at once
- Alternatives: is there a lower-cost path (configuration, operations, reuse of existing capability)
- Success criteria: **are KPI-/G- verifiable**; missing ones count as a major defect

Stage summary: **Worth doing / Not worth doing / Judge after more information is supplied** (the latter two usually map to FAIL or BLOCKED)

### Stage 2: Logic review (run when the value is debatable or worth doing)

- The goal -> solution -> acceptance chain is complete and consistent end to end
- User roles and permissions: all scenarios covered; no privilege-escalation or missing-permission paths
- Main flow + exceptions + boundaries: empty state, error state, no-permission state
- **BR-** items do not contradict each other; state machines / transitions are closed
- Fields / data definitions: numerator and denominator, data source, refresh frequency
- Dependencies and assumptions are explicit; **scope and non-scope** are clear; the responsible party for cross-system / API items is clear

Stage summary: **Logic closed / Logic has gaps / Logic inconsistent**

### Stage 3: Clarity review (throughout the whole text)

Points that design / development / test cannot act on directly are numbered **Q-001, Q-002...** (type: value / logic / clarity):

- Vague words: "appropriate", "optimize", "and related", "etc.", "as the case may be", "good experience"
- Feature descriptions without AC-; missing field / state / permission definitions
- Prototype and written PRD conflict with no statement of which prevails
- OP- items scattered around, with no Owner, or blocking development without being flagged

## Conclusion model

| Conclusion | Meaning | To Leader |
| --- | --- | --- |
| **PASS** | No Must Fix; Suggest/Nit allowed | Professional review passed; verification is still required; development must not start while OP- items are open |
| **FAIL** | Must Fix exists (including fatal value flaws, logic gaps, clarity blockers) | Assign PM: revise with `multica-pm-requirement-spec` -> `multica-pm-artifact-publish` Workflow B -> re-review |
| **BLOCKED** | Insufficient material or conflicting context; cannot review reliably | Re-dispatch after material is supplied; **does not count** toward the 3 FAIL rounds |

BLOCKED conditions: see [`references/review-workflow.md`](references/review-workflow.md#blocked).

## Issue severity

| Level | Description |
| --- | --- |
| **Must Fix** | Blocks (FAIL); fatal value flaws, logic inconsistency, untestable AC, OP- items that block development |
| **Suggest** | Maintainability, clearer wording, more robust boundaries |
| **Nit** | Wording, formatting; may be marked "can be ignored" |

Each item must include: **Problem** / **Impact** / **Suggestion** / **PRD location** (section, or G-/FR-/BR-/AC-/OP- ID).

## Output

Use the template in [`references/report-template.md`](references/report-template.md). Short header:

```text
[PRD Review] <link>
Conclusion: PASS / FAIL / BLOCKED
Value judgment: worth doing / not worth doing / pending
Logic judgment: closed / has gaps / inconsistent
Must Fix / Suggest / Nit / Q- list ...
Round: N / 3 (BLOCKED does not count toward FAIL rounds)
```

## Post-review revision loop (division of work with PM)

| Conclusion | ProductReviewer | ProductManager |
| --- | --- | --- |
| **FAIL** | Output Must Fix; **do not edit the PRD** | Leader assigns: spec revision -> publish **Workflow B** -> request re-review |
| **PASS** | Report to Leader | Development still must not start while OP- items are open |
| **BLOCKED** | List the missing items | Leader/human supplies the material |

**PASS is not G1 passed.** Do not notify downstream yourself, do not create/update JIRA/Confluence, do not @ other Agents.

## Review principles

- Read the whole text first, then conclude; never judge from titles or summaries alone
- Every issue is traceable to a location in the PRD text
- Do not pass a requirement with fatal flaws just to be friendly
- Without clear evidence, mark it "risk / question" rather than asserting it is wrong
- Even on PASS, record the key points checked and any residual OP-/Suggest risks

## Boundaries

- Review only the PRD/requirements, not design, code, tests, or UI
- Does not replace Leader's `multica-verification`
- Technical feasibility goes to ArchReviewer
- Still FAIL at round 3 -> mark "escalate to human" and hand to Leader
