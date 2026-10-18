# Automation Assets Lifecycle (Apifox + Playwright + Git)

Pairs with `docs/test-automation-in-repo.md`; @Tester starts accumulating in T1/T2 and executes in T3.

---

## Overview

```text
T1  Full-text cases in Confluence + Apifox scenarios (contract in parallel)
    ↓ human review + go-ahead
    XMind → test-management platform (optional)
T2  Confluence increment + Apifox supplemental scenarios + e2e skeletons checked in per MULTICA §2
T3  Run Apifox CLI + pytest on the deploy environment (e2e_dir from MULTICA) → fixes are committed to the deploy branch
```

---

## Apifox (API)

| When | Action |
| --- | --- |
| T1 in parallel | After the API contract is published: read `openapi.json` / the Confluence contract → supplement scenarios via `multica-platform-apifox` (**AI branch**; see openapi-branch-workflow.md) |
| T2 | Append endpoint scenarios per the supplement list; update `tests/api/<ISSUE-KEY>/manifest.json` |
| T3 | `multica-test-t3-api-automation` → `run_apifox.py`; scenarioIds come from the manifest or Issue comments |

**Forbidden**: importing API cases into JIRA; the main steps live only in Apifox.

---

## Playwright (UI)

| When | Action |
| --- | --- |
| T1 | Write CASE-ID, steps and expected results clearly in Confluence (**no scripts**) |
| T2 | For CASEs on the T2 list that **must** be automated: create a skeleton at `{e2e_dir}/test_{case_id}.py` (locators may be TODO → T3 BLOCKED if still missing) |
| T3 | `pytest {e2e_dir}/` against deploy_url; FAIL → t3-failure-triage → fix script and commit |

Framework: reuse `multica-test-t3-ui-automation/references/framework-template.md`; **target directory = the UI E2E path in MULTICA.md §2**; do not create a temporary directory each time.

---

## Git merge

- **Path**: root **MULTICA.md** §2 of each repo (when split, read each repo's own MULTICA)
- **Branch**: same as the Issue deploy branch; commit before G2
- **Commits**: e2e scripts, manifest; never commit `.env`

---

## Confluence vs XMind (current policy)

| Stage | XMind |
| --- | --- |
| T1/T2 phase A | **Not generated** |
| Phase C after the human go-ahead | `generate_xmind.py` → `import_to_tracker.py` |

Confluence is the **primary copy for review and collaboration**; the JSON may be a working file for generation/import and need not be presented externally as a deliverable.
