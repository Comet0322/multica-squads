# T1 Case Import Contract (import_to_tracker.py)

> This skill **does not ship** a bulk import script — it is tightly bound to a specific test-management platform (Jira case plugin / TestRail / Zephyr / in-house platform…) and cannot be generalized.
> Teams implement `import_to_tracker.py` for the platform they use; **meeting the contract and hard constraints below** is enough to plug into the T1 flow seamlessly.

## Interface convention

| Parameter | Meaning | Constraint |
| --- | --- | --- |
| `--jira-url` | Full URL of the target requirement Issue | Required |
| `--input` | `test_cases.json` (T1 structured cases, see `output-format.md`) | Required; **functional cases only** |
| `--suite-name` | Test suite name | **Required and unique**; naming rules in `generation-workflow.md` |
| `--dry-run` | Preview without actually writing | Optional |
| `--manual` | Confirm one by one | Optional |
| `--update-existing` | Update descriptions of existing cases | Optional |

Optional output: return the case-set URL, which the Tester writes back to the Issue (Relates) + updates the Confluence status to "Imported to JIRA".

## Hard constraints (consistent with the T1 flow)

1. **Run only after a human passphrase**: execute only on an explicit import instruction (e.g. "Review approved, import to JIRA"); after Phase A publishes to Confluence, **do not** skip review or generate XMind in the same turn.
2. **Import only once per batch**, into **one** test suite only; no repeated runs, no secondary link scripts.
3. **API cases are never imported** (API cases go through Apifox + manifest).
4. **Relates closed loop**: requirement (Story) <-> case set (Task) via Relates only; no Include fan-out for cases; the requirement panel links the case-set Task, not the Story.
5. **Pre-import validation**: confirm the JIRA Key, confirm it has not been imported yet, confirm `--suite-name` is unique, confirm the name strictly corresponds to the requirement.
6. **Post-import link validation**: self-check against the Relates rules above (refer to live examples).

## Failure handling

- Already imported: do not import again; report the existing case info directly.
- Any validation failure: stop and report BLOCKED; do not fabricate.
