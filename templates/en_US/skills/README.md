# Skills Index (en_US)

This directory collects the shared Skills that can be mounted directly into [Multica](https://github.com/multica-ai/multica), **grouped by role** (`architect/` / `backend/` / `designer/` / `devops/` / `frontend/` / `leader/` / `platform/` / `product-manager/` / `reviewer/` / `shared/` / `tester/`). **Each Skill is a subdirectory of its group**; `SKILL.md` is the skill description for the Agent to read; Skills with scripts also ship a `README.md` giving a human-oriented quick start.

Grouping is only **how the repo is organized** and is unrelated to capability layering: mounting only looks at the `name` in `SKILL.md`, and one group may span the content / orchestration / platform / review layers (for example `platform/` is entirely the platform layer, while `tester/` holds content + orchestration).

Layering model (see `docs/en_US/role-skills-architecture.md`): **content** (what "good" means) + **orchestration** (landing artifacts on team platforms) + **platform** (the only layer touching external systems) + **review** (executed by non-producers).

## 1. Platform layer (Platform, including placeholder shells; real URLs / credentials are supplied by the user in `.env`)

| Skill | Purpose | Main entry |
|---|---|---|
| `multica-platform-confluence` | Read/write Confluence pages (URL / pageId -> Markdown + images) | `scripts/confluence.sh`, `scripts/publish_design.py`, `scripts/fetch_page_by_url.py` |
| `multica-platform-jira` | Read/write JIRA issues, comments, status transitions, linked issues | `scripts/jira.sh`, `scripts/get_issue.py` |
| `multica-platform-jenkins` | Trigger Jenkins builds / releases / promotions | `scripts/trigger_env.py`, `scripts/build_sit.py`, `scripts/promote_prod.py` |
| `multica-platform-apifox` | Sync OpenAPI, add scenarios, run batches | `lib/apifox.js`, `scripts/run_apifox.py` |
| `multica-platform-figma` | Read Figma file metadata / design summaries | `scripts/fetch_file.py` |
| `multica-platform-git-host` | Open a PR/MR on the code host (Forgejo, GitLab, Azure DevOps); opens only, never merges | `scripts/open_pr.py` |
| `multica-platform-knowledge-base` | Query the team wiki knowledge base via a Bridge HTTP endpoint (Q&A / entry paths / terms) | `scripts/kb_ask.py` |

## 2. Orchestration layer (Orchestration, calls the platform layer to land artifacts and return stable links)

| Skill | Purpose | Main entry |
|---|---|---|
| `multica-pm-artifact-publish` | PRD / requirements -> `docs/prd/<ISSUE-KEY>.md` in the product repo (Git version) | (pure orchestration) |
| `multica-artifact-architect` | Technical design -> `docs/design/<ISSUE-KEY>/design.md` in the product repo (Git version) | (pure orchestration) |
| `multica-artifact-backend` | API contract -> team API platform (Apifox by default) | (pure orchestration) |
| `multica-design-ui-impl` | UI spec -> team design platform (Figma by default) | (pure orchestration) |
| `multica-artifact-frontend` | Frontend implementation spec -> `docs/frontend/<ISSUE-KEY>/impl-spec.md` in the product repo | (pure orchestration) |
| `multica-artifact-cicd-sync` | Code-review verdict -> trigger CI (Jenkins by default), return the deploy URL | `scripts/trigger_cicd.py` |

## 3. Content layer (Content, defines the standard of "good")

| Skill | Purpose |
|---|---|
| `multica-pm-requirement-spec` | Requirements analysis: structure requirements into a numbered PRD |
| `multica-technical-design` | Technical design draft (with metadata and revision log) |
| `multica-backend-impl` | Backend implementation: contract first + TDD |
| `multica-frontend-impl` | Frontend implementation: complete experience and states |
| `multica-verification` | Generic Leader gate: is the evidence complete, is the AC correct |
| `multica-test-orchestration` | Cross-stage test routing (T1/T2/T3) and verdicts |
| `multica-test-t1-design` | T1 functional cases: traceability matrix + coverage dimensions |
| `multica-test-t2-coverage` | T2 coverage assessment (against T1 and the implementation diff) |
| `multica-test-t3-ui-automation` | T3 UI automation (1 CASE = 1 test) |
| `multica-test-t3-api-automation` | T3 API automation batch runs |

## 4. Review layer (Review, executed by non-producers)

| Skill | Purpose |
|---|---|
| `multica-review-product` | Product / value review |
| `multica-review-architect` | Architecture review |
| `multica-review-designer` | UI / interaction review |
| `multica-review-frontend` | Frontend review |
| `multica-review-backend` | Backend review |
| `multica-review-test` | Test review |

## 5. Collaboration and tooling (Shared / Tooling)

| Skill | Purpose |
|---|---|
| `multica-handoff-protocol` | Shared handoff protocol for members: plain-text delivery comment, no @mention of the Leader, only the Leader changes status |
| `multica-manage-skills` | Manage Skills through the Multica API |

## 6. How to mount into Multica

1. Copy the Skill directories you need, as a whole, under the `skills/` of your Multica workspace (the directory name is the Skill name and must match the `name` field in `SKILL.md`).
2. For Skills with scripts: first `cp .env.example .env` and fill in your own `JENKINS_URL` / `JIRA_URL` / `CONFLUENCE_URL` / `ATLASSIAN_USER` / `ATLASSIAN_PASS`, etc., then install dependencies and run the examples following that Skill's `README.md`.
3. **Never commit real values** for platform-layer URLs / credentials - keep the `.env.example` placeholders only.

## 7. Naming conventions

- Uniform `multica-` prefix + lowercase hyphenated.
- The platform layer holds placeholder shells only; real infrastructure information is supplied by the user in `.env`.
