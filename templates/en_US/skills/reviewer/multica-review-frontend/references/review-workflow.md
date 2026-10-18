# Frontend Review Workflow

FrontendReviewer executes in this order after receiving a dispatch from the Leader. For detailed checklist items see [`checklist.md`](checklist.md).

## 1. Lock materials

- Read the Multica Issue, latest comments, and the @FrontendDev completion note and attachments
- Read what the Leader explicitly provides: impl-spec (repo link), UI link, API contract, AC-
- Confirm the **project repository** path and diff range (the Multica task workdir is temporary context only, not the review root)

## 2. Verify scope

- Compare the changed-file list with the actual diff and confirm it matches the issue goal
- If the project has a README / `.cursor/rules` / internal frontend conventions, load them as the review baseline

## 3. Review against the checklist

- Check item by item (UI flow, states, contract, types, patterns, impact surface, tests)
- Run lint / unit tests / type checks when needed; record the reason when they cannot be run

## 4. Grading and verdict

- Classify issues as Must Fix / Suggest / Nit
- Any Must Fix -> **FAIL**; no Must Fix and a complete review -> **PASS** (may carry Suggest/Nit)
- A BLOCKED condition is hit -> **BLOCKED**; do not force PASS/FAIL

## 5. Output and report to the Leader

- Use the output template in SKILL.md
- Do not @FrontendDev to change code yourself; the Leader assigns that

## BLOCKED (stop first, then judge)

In the following cases output **BLOCKED**, list what is missing, and do **not** count it toward the 3 FAIL rounds:

| Condition | Description |
| --- | --- |
| Claimed change cannot be found | The diff / file list does not match the completion note |
| Diff clearly does not match the issue goal | Change scope deviates from the AC or impl-spec |
| Upstream descriptions conflict | JIRA / Confluence / Issue statements contradict each other and affect the judgment |
| AC or acceptance criteria unclear | Cannot objectively judge whether the implementation is correct |
| Missing required context or permissions | Cannot read the repo, contract or UI |
| Change too large | A single review cannot cover it reliably; the Leader must split the scope |

BLOCKED vs FAIL: FAIL = materials are sufficient and Must Fix items exist; BLOCKED = **a reliable review could not yet be started or completed**.

## Re-review

1. Read the previous round's Must Fix list
2. Check each item for resolution
3. Unresolved items remain Must Fix; new issues are added by grading
4. Round +1 (only a FAIL re-review counts as a round; a re-review after supplying materials following BLOCKED does not count the previous FAIL)
