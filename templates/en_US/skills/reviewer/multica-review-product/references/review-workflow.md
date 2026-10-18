# PRD Review Workflow

ProductReviewer executes in this order after receiving a dispatch from the Leader. For checklist items see [`checklist.md`](checklist.md); for the report see [`report-template.md`](report-template.md).

## 1. Lock materials

- Read the PRD link from the Leader's dispatch (returned by `multica-pm-artifact-publish`) + the original Issue text
- Optionally read: prototype, data definitions, dependency notes
- When needed, call `multica-platform-confluence` / `multica-platform-jira` read-only to fetch the full text
- Optionally call the `team knowledge base (optional)` to check terms (**no rule extrapolation**)

## 2. Verify readability

- The full PRD is accessible and consistent with the Issue goal
- A BLOCKED condition is hit -> stop, list what is missing, report to the Leader

## 3. Three-stage review (no skipping)

1. **Value judgment** - problem reality, ROI, phasing, alternatives, KPI- / G-
2. **Logic review** - goal -> solution -> acceptance, permissions, main / exception flows, BR-, definitions, scope, cross-system boundaries
3. **Clarity review** - vague words, missing definitions, text/diagram conflicts, OP-; produces Q-001...

## 4. Grading and verdict

- Classify issues as Must Fix / Suggest / Nit
- Any Must Fix -> **FAIL**
- No Must Fix and a complete review -> **PASS** (may carry Suggest/Nit and residual OP- risks)
- Insufficient materials -> **BLOCKED**

## 5. Output and report to the Leader

- Output the full report per report-template
- **Report only to the Leader**; do not @ProductManager, do not DM, do not push development scheduling

## 6. Re-review

- Check the previous round's Must Fix items one by one
- Round +1 (only a FAIL re-review counts as a round; a re-review after supplying materials following BLOCKED does not count the previous FAIL)

## BLOCKED

In the following cases output **BLOCKED**, list what is missing, and do **not** count it toward the 3 FAIL rounds:

| Condition | Description |
| --- | --- |
| No PRD link, or the full text is inaccessible | Cannot read Confluence/JIRA/body text |
| Issue and PRD goals clearly inconsistent | Wrong document reviewed |
| Upstream descriptions conflict | JIRA / Confluence / Issue statements contradict each other; cannot judge |
| Missing Story Key or business background | Cannot judge value/scope and the Leader did not provide it |

BLOCKED vs FAIL: FAIL = materials are sufficient and Must Fix items exist; BLOCKED = a reliable review is not yet possible.
