# T3 Merged Report Template

> Produced by `multica-test-orchestration` once evidence from both the UI and API sides is complete (or one side is runnable). Maps to **G3**.

```markdown
# T3 Acceptance Test Report - {JIRA_KEY}

## Overall verdict
**PASS | FAIL | BLOCKED**

> If either side is BLOCKED and its ACs cannot be covered by the other side -> the overall verdict must not be PASS.

## Environment
- G2.5: {PASS | N/A | not passed}
- deploy_url: {url}
- page_url: {url or same as deploy}

## Channel summary
| Channel | Verdict | Evidence |
| --- | --- | --- |
| UI (pytest+Playwright) | PASS/FAIL/BLOCKED/N/A | case_map.md / Allure |
| API (Apifox CLI) | PASS/FAIL/BLOCKED/N/A | run_apifox JSON / logs |

## Per-AC verdicts
| AC- | Result | Evidence source |
| --- | --- | --- |
| AC-1 | PASS/FAIL/BLOCKED | UI-xxx / Apifox-xxx / manual appendix* |

*Manual appendix: only with the Leader's written authorization; the title must read "Not automated, does not replace G2.5"; it **must not** be used to rule the overall automation verdict PASS.

## FAIL details (if any)
- AC-x: reproduction / expected / actual / severity / evidence path

## BLOCKED / out of scope (if any)
- …

## Attachments
- UI: …
- Apifox: …
```

## Routing reminder

| Situation | Behavior |
| --- | --- |
| Only UI materials complete | Run UI only; the three Apifox IDs are marked N/A and do not count as missing |
| Only API materials complete | Run Apifox only |
| Both complete | Run both, then merge |
| One side missing materials | That side is aborted; the other side may run; the overall verdict must not be PASS |
| G2.5 N/A and no deploy_url | Automation on both sides is BLOCKED |
| G2.5 N/A but deploy_url present + Leader written approval to run | May run; the report notes the G2.5 downgrade |

## Manual appendix (when authorized by the Leader)

- May list manual step results, titled **"Not automated, does not replace G2.5"**
- The overall automation verdict stays **BLOCKED** unless all ACs have been fully verified in the deployed environment (confirmed in writing by the Leader)
