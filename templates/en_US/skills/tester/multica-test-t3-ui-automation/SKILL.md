---
name: multica-test-t3-ui-automation
description: "T3 UI automation: pytest+Playwright, 1 functional case = 1 e2e test; paths from MULTICA.md §2; run on the deploy URL only after G2.5 PASS; joined with the API side into one verdict. No local mock."
version: 1.2.0
metadata:
  orchestrates:
    - multica-test-orchestration
---

# Test UI Automation (functional case -> UI 1:1)

Run the Playwright cases of **T1 Confluence / T2 in-repo** on the **deployed environment**.

> T2 should write / accumulate scripts under the **MULTICA.md §2 UI E2E path** (see `docs/test-automation-in-repo.md`). For the T3 gate see `multica-test-orchestration`.
>
> T3 only after **G2.5 PASS**; an AC that can only be verified by UI -> run this skill alone; if it also has an API channel -> run both, orchestration merges one report. **Material assembly + BLOCKED: see `multica-test-orchestration`.**

## Platform collaboration

| Platform skill | Use in this skill |
| --- | --- |
| — | No direct platform call; `page_url` / the case set come from Issue comments and T1 artifacts |

The UI runs on the deployed environment; the environment URL is written by DevOps / Leader into the JIRA comment (see `multica-artifact-cicd-sync`).

## Principles

- **In-repo path**: Read the target repo's **MULTICA.md §2** (for split repos, read one copy each per the Issue matrix); missing file -> BLOCKED
- **No e2e directory yet**: initialize it at the path MULTICA specifies per `framework-template.md` (`/tmp/ui-auto-*` is forbidden)
- **Forbidden prerequisites**: `xmind-ui-automation`, `req-figma-ui-automation`, the company's **external `playwright.git` repository** (not in conflict with this repo's MULTICA §2 path)
- **1:1**: every automated CASE -> exactly one `test_*.py`
- **Step alignment**: `steps[i]` -> the i-th action; `expected_results[i]` -> the assertion of that step (equal length)
- **No fabrication**: locators come from the real page **after opening page_url**; not found -> **BLOCKED**

## Required items (stop + interruption list if missing; summary from comments)

| Required | How it counts as complete |
| --- | --- |
| G2.5 PASS | Leader/DevOps explicit G2.5 PASS (or deploy_url + Leader written authorization) |
| deploy_url | Reachable environment URL |
| page_url | Page URL; if omitted must equal deploy_url (state it in the comment) |
| e2e script | **Path in MULTICA.md §2**; in the deploy branch at the G2.5 SHA, **1:1** with the cases |
| ui_auth | `auth_mode=none` or "account via Secret variable name"; **never a plaintext password taken from comments** |

## Input (interrupt if missing)

```text
repo_root:               # Issue repo matrix; Read MULTICA.md
e2e_dir:                 # MULTICA.md §2 UI E2E path (default tests/e2e/)
cases_source:            # T1 Confluence or test_*.py inside e2e_dir
page_url / deploy_url:   # Issue comment
jira_key:
auth_mode:               # none | form_login | sso | cookie
auth_user_env / auth_pass_env:
```

### Account and password (mandatory)

- `page_url` **does not mean** logged in; a system that requires login must provide `auth_mode` + env variable names
- **Never** write account / password into: case JSON, scripts, XMind, JIRA comments, Allure body
- Case preconditions state only the permission semantics; real credentials live only in Agent Secret / a gitignored `.env`
- Before execution check that `auth_user_env` / `auth_pass_env` are non-empty; empty -> interrupt, prompt to configure the Secret and **do not paste it back into the Issue**
- `auth_mode=none`: pages that need no login only
- `auth_mode=cookie`: local `storage_state` path; never paste cookies into comments

Unconfirmed, no URL, login required but env empty, steps/expected of unequal length -> stop.

## Flow

### Phase A — Confirm the case set

1. Read only `functional` (ignore `api`)
2. Validate `len(steps)==len(expected_results)` and non-empty
3. List the case_id -> test method mapping table (count = number of functional cases)

### Phase B — Framework (e2e_dir)

If `{repo_root}/{e2e_dir}/` has no `pytest.ini`: generate it **in that directory** per `framework-template.md`.  
If this skill's skeleton already exists -> add cases incrementally.  
Do not create a parallel playwright project outside the repo.

```bash
cd {e2e_dir}   # MULTICA.md §2 UI E2E path
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/playwright install chromium
```

### Phase C — One-to-one generate / complete

T2 should already have built the skeleton; T3 fills in locators and fixes assertions. Rules in [`references/case-mapping.md`](references/case-mapping.md).

### Phase D — Execute

```bash
cd {e2e_dir}
.venv/Scripts/pytest . -q --alluredir artifacts/allure-results
# or, against the deployed page:
pytest <MULTICA.md §2 e2e path> --base-url <page_url> --alluredir ./reports/ui
```

Cases source: T1 Confluence t1-cases + T2 supplement. Missing script path -> interruption list.

## Output

| Artifact | Description |
| --- | --- |
| `{e2e_dir}/` changes | **Commit to the deploy branch** (also after a FIX) |
| `artifacts/case_map.md` | case_id <-> file <-> result |
| Allure / pytest log | Per-case PASS/FAIL/SKIP(BLOCKED) |
| **Issue comment** | Mapping table + commit SHA + failure details |

Report template:

```markdown
# T3 UI Automation — {JIRA_KEY}
- G2.5: PASS @ {sha}  deploy: {url}  page: {page_url}
- e2e: {MULTICA.md §2 path}
- total / pass / fail / error
- per case: id / title / status / screenshot / log path
- conclusion: PASS | FAIL | BLOCKED
```

This skill **does not issue a PASS verdict on the whole ticket's AC**; the overall T3 report is merged by `multica-test-orchestration`. It merges with the API side: **if only one side verifies a given AC and that side is missing -> the whole ticket cannot be PASS**.

## FAIL / ERROR triage

When UI automation FAILs: **@Tester** triages per `multica-test-orchestration/references/t3-failure-triage.md`. Wrong locator / steps -> Tester fixes; page behavior contradicts the AC -> dispatch FrontendDev. Frontend must not edit pytest to lower the bar before triage.

## Prohibitions

- Using `xmind-ui-automation`, `req-figma-ui-automation`, or an **external playwright.git in place of this repo's MULTICA §2 e2e directory**
- Cases that exist only in a temp directory and never enter Git
- Splitting one functional case into several tests, or merging several into one
- Putting API requests into UI cases (APIs go through Apifox)
- Treating results as T3 PASS before G2.5
- Writing a plaintext password into an Issue or script

## Why it works

UI verification is bound to the actual deployed page; 1:1 with the cases avoids "runs but doesn't cover"; running after G2.5 avoids a green build masking a broken environment.
