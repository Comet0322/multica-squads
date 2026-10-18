# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

## 0.2.0 - 2026-10-19

Verified end to end on a test repo with the reviewed starter and the bug-fix starter: backend, frontend, fullstack, epic with slices, concurrent Issues, UI design, bug fix. Highlights: PR opening and close-after-merge, epic and slices, fresh-against-main re-gating, UI design requestable from the Issue, agents stop the servers they start.

### Changed

- **UI design can now be requested in an Issue**: the spec template (and both starters' `issue.md`) splits the Scope end "Design (needs Architect)" into "Design (needs Architect: technical design)" and "UI design (needs Designer)"; `check_spec.py`, the PM skill and both `squad.md` G0 routing text follow. Before, a human could not ask for the Designer, and the Leader scoped a UI feature's design to the Architect only.

### Added

- **Fresh against `main` before the PR** (`leader.md` [Open PR], `FLOW.md` §4.4): when `main` moved while an Issue was running, the Owner merges it into the delivery branch and resolves conflicts, and the Leader re-gates that head before opening the PR. Observed in a two-Issue run that edited the same response: the second Issue absorbed the first and re-gated.

- **Agents stop what they start**: `frontend-developer.md` and `tester.md` forbid leaving dev servers or browsers running and reusing servers they did not start; `MULTICA.md` §2.2 requires the Playwright config not to reuse an existing server. Found when a stale Vite on the test port blocked T3.

## 0.1.0 - 2026-10-19

First tagged state: English-only templates, Git-flow aligned skills, spec chat with one enforced format, PR opening and close-after-merge, epic and slice splitting (untested end to end).

### Added

- **Large changes split into an epic and slices**: the ProductManager's size check (spec chat step 3b) proposes vertical, independently shippable slices that the human approves before anything is created. The epic is a parent Issue never built itself; slices are sub-issues ordered with Multica's native `--parent` and `--stage` and created unassigned for later stages. The Leader's new [Epic] section assigns each stage after the previous one is merged and `done`, and leaves the epic `in_review` at the end. `FLOW.md` §4.5, both starters' G0 section and `multica-pm-requirement-spec` describe it.
- **Close an Issue after the human merges the PR**: `multica-platform-git-host` gains the read-only `scripts/pr_status.py` (open / merged / closed, head and merge SHA on Forgejo/Gitea, GitLab, Azure). The Leader's new [Close after merge] section sets `done` only when the PR is merged at the gated Head SHA; both starters' G4 line and `FLOW.md` §4.4 describe it.
- **One source for the spec format**: `multica-pm-requirement-spec/references/spec-template.md` is the canonical Issue/spec template and `scripts/check_spec.py` enforces it (one source ticked, involved ends, numbered testable AC-, no vague words, every OP- closed with the human's answer or acceptance; `--issue <KEY>` fetches an Issue, `--sync-check` verifies copies). Both starters' `issue.md` carry a verbatim copy. The ProductManager follows the skill's Chat mode when a human picks the skill with `/` in a chat (it is named in the agent's instructions too), grounds itself in the project's repo, and runs the check before creating an Issue; the Leader runs the same check at G0 (the skill is now bound to the Leader).
- **G0 exception for spec chats**: an Issue filed by the ProductManager after a spec chat (Notes carry the line "Spec chat: …confirmed by the human in the chat", `check_spec.py` PASS, no open OP-) passes G0 without a further human confirmation; the Leader still posts the routing map and deploy branch for information (both starters' `squad.md`, `leader.md`, `multica-pm-requirement-spec`).
- **ProductManager chat mode**: a human can discuss a spec with the ProductManager in a chat; the agent interviews one question at a time, shows the draft, and only after an explicit "create it" files a fully self-contained Issue for the squad (`product-manager.md` [CHAT MODE], `multica-pm-requirement-spec` Chat mode, reviewed starter README). The Leader then skips the PRD stage.
- **`docs/en_US/FLOW.md` §4.0 "Handoff (Owner ↔ Leader)"**: FLOW now specifies the Owner→Leader handoff (`**Delivery**` comment in plain text, no mention link; the platform wakes the Leader automatically), leaves status to the Leader's gate decision, and defines blocked/rework formats. The protocol lives in the shared skill `multica-handoff-protocol`, bound to all members except the Leader; each member's completion section points to it.
- **The Leader opens the PR after all gates PASS** (`templates/en_US/agents/leader.md` rule 11 and [Open PR] section, `docs/en_US/FLOW.md` §4.4): the Leader opens the PR through the platform skill `multica-platform-git-host` (host type and PR-only token variable live in its `config.yaml`; the prompt holds no platform details); the body carries gate evidence, AC mapping and known limitations. The Leader never merges; humans merge on the protected `main` (merge allowlist). The Status comment records the PR link and the verified Head SHA.
- **New platform skill `multica-platform-git-host`**: `scripts/open_pr.py` opens a PR/MR on Forgejo/Gitea, GitLab or Azure DevOps, reuses an existing open PR for the same head, never merges; the repo comes from `origin` (the repo bound in Multica) and host type / token variable live only in `config.yaml`. Added to the Leader binding in `squad-bootstrap`.
- **`docs/en_US/FLOW.md` §4.4 "Open PR"** and the English Leader rule 11 / [Open PR] section added.

### Changed

- **`multica-backend-impl`, `multica-frontend-impl`, `multica-artifact-frontend` aligned to the Git flow** (v2.0.0-repo / 3.0.0-repo): upstream (Issue, PRD, design, API contract) is read from the product repo and the frontend implementation spec lands in `docs/frontend/<ISSUE-KEY>/impl-spec.md`; no Confluence / JIRA calls. `MULTICA.md` §1.1 gains the implementation-spec row.
- **Sanitized the JIRA / Confluence platform shells**: replaced real usernames, company and project names, page IDs, epic keys, center / region option labels and the DingTalk project mapping with generic placeholders (JIRA field IDs were left as they are).
- **Removed the Chinese (zh_CN) templates and docs; the repository is English-only (en_US).** Chinese-only platform scripts were ported into en_US. The Chinese backup is not part of the repo.
- **Unified gate labels** (both starters' `squad.md` and `gates-and-evidence.md`): S2 join = `G2-prep` (API contract + functional cases), S3 join = `G2` (frontend + backend + API cases), test gate = `G3`. Previously the S3 join clashed with the test gate under G3 (reviewed) or G2 (base).
- **`designer.md` no longer dispatches reviewers or @FrontendDev itself** and hands off to the Leader; `architect.md` / `leader.md` now name the reviewer neutrally (@Reviewer in the base starter, the dedicated Reviewer in the reviewed starter; the Squad Instructions are authoritative).
- **Rule gaps closed in `software-development-reviewed` `squad.md`**: a Tester N/A needs human confirmation at G0; re-review rounds caused by human decisions do not count toward the 3-round limit; only the Leader changes Issue status (`in_review` while waiting on a human); the Leader lists uncovered items at G4.
- **Issue templates (both starters) gain a "Testing (needs Tester)" scope item.**
- **Leftover CJK punctuation replaced with ASCII** in prose and docstrings (full-width brackets, colons, periods); the 【】 section markers and the knowledge-base bridge prompt are kept on purpose.
- **`multica-review-backend` review header names the phase** (contract at G2-prep or implementation at G2) so contract reviews are no longer labelled as implementation reviews.
- **`multica-review-frontend` lists ineffective tests as Must Fix.**
- **`multica-pm-artifact-publish` is now Git-based**: the PRD is written to the product repo (`docs/prd/<ISSUE-KEY>.md`) and pushed to `release/<ISSUE-KEY>-<slug>` instead of Confluence / JIRA (the company has no such platforms). The previous Confluence + JIRA version is in git history.
- **`multica-artifact-architect` / `multica-artifact-backend` are now Git-based**: the design is written to `docs/design/<ISSUE-KEY>/design.md` and the API contract to `docs/backend/<ISSUE-KEY>/api-contract.md`, pushed to the deploy branch with the link returned, instead of Confluence / JIRA / Apifox. The section self-check tables are kept.
- **`MULTICA.md` gains an "Artifact paths" table (§1.1)**: PRD / design / API contract / case paths are declared in one place; the Git-based PM / Architect / BackendDev skills defer to it so roles stop inventing paths. The `Related repos` column says to enter N/A for a single repo.
- **Tester moves to a Git flow**: `multica-test-orchestration` is rewritten — T1 cases go to `docs/test/<ISSUE-KEY>/t1-cases.md`, API cases land in `server/tests/acceptance/`, the T2 assessment goes to `t2-coverage.md`, the T3 report to `t3-report.md`; `t1-design` / `t2-coverage` / `t3-api-automation` / `multica-review-test` get a Git-flow banner at the top and ignore JIRA / Confluence / XMind / Apifox steps. `tester.md` resolves the T3 contradiction: when the Leader judges G2.5 N/A, it falls back to local real execution, clearly flagged, with the verdict capped at "PASS (local)". The handoff summary in every agent's instructions now says plain text, no mention link.

## v0.0.17 - 2026-09-10 · Rename to internal names, drop gate-setup, publish knowledge-base

### Changed

- **5 skills renamed to match the current internal names** (the internal edition had already renamed them before the back-migration; the public edition was still on the old names):
  `multica-requirement-analysis` → `multica-pm-requirement-spec`; `multica-artifact-req-sync` → `multica-pm-artifact-publish`; `multica-artifact-design-sync` → `multica-artifact-architect`; `multica-artifact-api-sync` → `multica-artifact-backend`; `multica-artifact-ui-sync` → `multica-design-ui-impl` (internal v0.0.47). Both language trees synced; `name:` and all references across the repo (docs / README / squad / agents / configs) updated together.
- **Removed `multica-gate-setup`** (the internal edition never had this skill; the CI hard-gate concept is carried by `multica-artifact-cicd-sync` + `multica-verification`). The G2 "CI hard gate" narrative in `squad.md`, `gates-and-evidence.md`, `adapt-and-scale.md`, `README`, `AGENTS.md`, the skill index and configs now all points to `multica-artifact-cicd-sync`; the DevOps skill group in squad-bootstrap no longer lists it. Dangling links across the repo after removal: **0**.
- **Published `multica-platform-knowledge-base`** (migrated from the internal edition and desensitized): `http://192.168.34.138:3910` → `http://kb-bridge.example.com:3910`; `KB138_*` → `KB_*`; internal wording such as "138 Cursor Bridge / team knowledge base" generalized throughout. Added to the `platform/` layer table (skill index + zh/en architecture docs). Post-desensitization check: **0 occurrences of `138` / `192.168`**.
- **Added the 5 missing en_US testing skills** (`tester/` group, copied from zh_CN): `multica-test-orchestration` / `multica-test-t1-design` / `multica-test-t2-coverage` / `multica-test-t3-api-automation` / `multica-test-t3-ui-automation`. en_US goes from 18 → **22** skills, and the 3 previous dangling links are gone.

### Compared with internal after convergence

| Category | Description |
| --- | --- |
| Naming aligned | The 5 renamed skills now match the internal names |
| Removed | `multica-gate-setup` (not present internally; public-only → removed) |
| Added (desensitized, public) | `multica-platform-knowledge-base` (an internal red-line skill; published after generalizing the Bridge address and variables) |
| Still not migrated (red line) | `multica-design-ui-impl` (bound to BOSS / AngelAlign) — the public edition covers it with the content-layer `multica-frontend-impl` and does not include this implementation |
| Net count | zh_CN **29** (1 removed, 1 added, unchanged), en_US **22**; **0 broken** relative links repo-wide |

## v0.0.16 - 2026-09-10 · Group skills by role (align with internal layout)

### Changed

- **`templates/{zh_CN,en_US}/skills/` changed from flat to grouped by role**, matching the internal layout:
  `architect/`(2) · `backend/`(2) · `designer/`(1) · `devops/`(2) · `frontend/`(2) · `leader/`(1) · `platform/`(5) · `product-manager/`(2) · `reviewer/`(6) · `shared/`(1) · `tester/`(5) — zh_CN has **29** in total, en_US **18**.
- **All path references synced** (14 files): Starter READMEs (zh/en × 2 Starters), root README (zh/en), 6 docs in `docs/` (zh/en), and the skill index. Moved with `git mv` to preserve history; remaining flat-path references: **0**.
- Grouping is **only a way to organize the repo** and is unrelated to capability layering: mounting still goes only by the `name` in `SKILL.md`, and one group can span all four layers (e.g. `tester/` contains both content and orchestration layers).

### Compared with internal: what is extra / what is missing

| Category | Skill | Description |
| --- | --- | --- |
| Public edition **extra** | `multica-gate-setup` | Not in internal (CI hard-gate template, public-only) |
| Public edition **extra** | `multica-design-ui-impl` | No internal counterpart (the internal designer group only has `multica-design-ui-impl`) |
| In internal, **missing in public** | `multica-design-ui-impl` | Red line: bound to BOSS / AngelAlign, explicitly not migrated |
| In internal, **missing in public** | `multica-platform-knowledge-base` | Red line: bound to the 138 Bridge, explicitly not migrated |
| **Naming differences** (4 pairs) | `multica-artifact-backend` ← `multica-artifact-backend`; `multica-artifact-architect` ← `multica-artifact-architect`; `multica-pm-artifact-publish` ← `multica-pm-artifact-publish`; `multica-pm-requirement-spec` ← `multica-pm-requirement-spec` | The public edition uses the new names from v0.0.12 |

The other **23 match by name** (including `multica-review-test`, whose internal version likewise has no frontmatter).

## v0.0.15 - 2026-09-10 · Remove multica-implementation (split & superseded; align with internal)

### Removed

- **`multica-implementation`** (`templates/zh_CN/skills/` and `templates/en_US/skills/`): the internal edition had already **split and superseded** it with `multica-frontend-impl` (frontend: experience / state heavy) and `multica-backend-impl` (backend: TDD / contract-first heavy). The public edition still kept the directory, an **orphan missed during the back-migration**; after removal zh_CN actually has **29** skills. It was split into the two end-specific impl skills; the leftover directory was an orphan from the back-migration.
- **No general rules lost**: the original "read before editing" → `Before starting: read upstream (mandatory)`, "add appropriate tests" → `Before G2: unit tests (hard gate)`, "run verification / report actual evidence" → `Completion evidence` are all fully covered in the two impl skills.

### Changed

- **References synced (zh/en)**: agent templates (frontend / backend; "follow the method details in …" now points to their own impl skill), Starter README Step 2 (the Chinese version split into backend / frontend rows), root README flow diagram, skill index, `scripts/multica-sync/squad-bootstrap.example.json`
- **Architecture docs**: `docs/{zh_CN,en_US}/role-skills-architecture.md` list count stays **29** — the original 29 was right; the extra 1 was the root cause
- **Root README (zh/en)** skill count 30 → **29**

### Note

- This entry replaces the earlier workaround of "changing the docs to 30": the root cause of issue #4 was **something that should have been deleted but was not**, not a docs omission.

## v0.0.14 - 2026-09-10 · Fix corrupted apifox skill & missing frontmatter

### Fixed

- **Issue A (severe): `multica-platform-apifox` content corrupted by a global `a→p` replacement**: the desensitization bulk-replace rule in v0.0.12 went wrong, and 25 of 28 files in that directory were damaged — `name:` → `npme:`, `apifox` → `ppifox`, `install` → `instpll`, `api_base_url` → `ppi_bpse_url`, `sync_openapi.js` → `sync_openppi.js`, etc.; frontmatter, script references, command examples and config field names were all unusable, contradicting the README's "copy-paste and it works" promise.
  The whole directory was **re-exported from a clean source** (28 files, the file list identical to the corrupted version), and the internal domain was replaced **in a targeted way** (`apifox.<internal-domain>` → `apifox.example.com`, 10 files); **no global character substitution was done again**. The whole directory was re-exported from a clean source; only the internal host was replaced, no global character substitution.
- **Issue B (minor): `multica-review-test/SKILL.md` missing frontmatter**: the only one of the 30 zh_CN skills lacking `name:` / `description:`, so import tools could not read the name (falling back to the directory name) and the description (lost outright). Filled in following the en_US version, with the description rewritten from the Chinese body.

### Security

- Re-check: no company internal domains remain anywhere in `templates/`; all 30 SKILL.md files have full frontmatter; apifox corruption signatures are zero, and JS (12 files) and Python syntax checks pass
- Follow-up improvement: desensitization must **replace specific values in a targeted way**; unconstrained character-level global replacement over a whole directory is forbidden

## v0.0.13 - 2026-09-09 · Automation scripts: one-shot squad bootstrap

### Added

- **`scripts/multica-sync/`**: optional template-push automation (Python 3.9+, stdlib only) that pushes `templates/zh_CN` to a Multica workspace
- **`bootstrap_squad.py`**: the main one-shot squad bootstrap script, a 5-step idempotent pipeline — import skills → create/update agents → create squad → add members → bind skills; supports `--dry-run` / `--sync-skills` / `--bind-mode` / `--only` / `--runtime` / `--write-mapping`
- **`repo_paths.py`**: template path resolution (`templates/zh_CN` first, compatible with the flat layout; overridable via `MULTICA_TEMPLATES_DIR` / `MULTICA_TEMPLATE_LANG`)
- **`squad-bootstrap.example.json`**: full bootstrap config for 15 roles (role → skills mounts), using the repo's current skill names
- **Works with default config**: when `--config` is not passed, `bootstrap_squad.py` falls back to the built-in `squad-bootstrap.example.json`, so a squad can be built with as few as two commands

### Changed

- **`multica_client.py` extended**: added `create_squad` / `update_squad` / `add_squad_member` / `list_squads` / `create_agent` / `add_agent_skills` / `set_agent_skills` / `list_runtimes`
- **AGENTS.md / README (zh/en)** repo structure now describes `scripts/`, and the core conventions add "automation is config-driven and secret-free"
- **5-minute quick start split into two modes**: **Mode A automatic** (script, one command builds the whole set) / **Mode B manual** (copy-paste Steps 1–3); Steps 4–6 (create Issue → assign → run) are shared by both modes
- **Main flow wording fixed (zh/en)**: `requirement convergence (G0) → design → implementation → unit tests → deployment → automated tests` — the former "testing" is now explicitly **unit tests** (done within the implementation stage), and **automated tests** (T3) are explicitly placed **after deployment** (corresponding to G2.5 deploy → T3 run automation)
- **Tagline tweak (zh/en + AGENTS)**: `Copy. Paste. Run.` is followed by "ready to use after copying; or build the whole set automatically with one command", covering the script mode

### Security

- **Desensitization**: the scripts embed no host / token / workspace / ID; address resolution order is `--url` > `MULTICA_API_URL` > `config.local.json` (git-ignored)
- The join key is the **name** (agent / skill / squad name), so no UUID needs to be committed; all example values in `agent-mapping.example.json` are now placeholders

## v0.0.12 - 2026-09-05 · Internal back-migration batches 2–4: full skill back-migration + desensitization closed-loop

### Added (back-migrated from the internal edition, desensitized)

- **10 new skills (zh_CN)**: `multica-backend-impl`, `multica-frontend-impl`, `multica-artifact-frontend`, `multica-test-orchestration`, `multica-test-t1-design`, `multica-test-t2-coverage`, `multica-test-t3-ui-automation`, `multica-test-t3-api-automation`, `multica-platform-apifox`, `multica-platform-figma`
- **15 existing skills upgraded (zh_CN, overwritten in place with the more mature internal content)**: `multica-review-*` (×6), `multica-technical-design`, `multica-verification`, `multica-artifact-cicd-sync`, `multica-platform-jira`, `multica-platform-confluence`, plus the 4 already renamed in the internal edition: `multica-pm-requirement-spec`→`multica-pm-requirement-spec`, `multica-pm-artifact-publish`→`multica-pm-artifact-publish`, `multica-artifact-architect`→`multica-artifact-architect`, `multica-artifact-backend`→`multica-artifact-backend`
- **`MULTICA.md` mechanism landed**: product-repo root context template (layout / test automation paths / build and verify commands / branch conventions), one per repo when split, missing means BLOCKED

### Changed

- **Removed 3 superseded skills (zh + en)**: `multica-test-design`, `multica-test-automation`, `multica-artifact-test-sync`, all superseded by `multica-test-orchestration` + `multica-test-t1/t2/t3-*`
- **Global references updated**: agents / squad (zh+en) / docs (zh+en) / README (zh+en) / skills index all point to the new skill names; capabilities not shipped such as `multica-design-ui-impl` and `multica-platform-knowledge-base` are marked "optional, not shipped in this repo"
- **Desensitization closed-loop**: internal domains / IPs / domain-account variables / business system names / project keys / 138 Bridge all replaced with placeholders or generic examples; credentials and platform base URLs always go through env vars / `.env` (e.g. `JIRA_USERNAME`, `ATLASSIAN_PASS`, `APIFOX_API_BASE_URL`, `TEAM_KB_URL`)
- **`templates/zh_CN/skills/README.md`** rewritten as a four-layer (content / orchestration / platform / review) index
- **ROADMAP red lines updated**: explicitly states `multica-implementation` is kept (not superseded)

### Migration notes

- **Not migrated** (bound to company-internal systems, recorded in the ROADMAP red lines): `multica-design-ui-impl` (BOSS master / AngelAlign), `multica-platform-knowledge-base` (138 Bridge), `import_to_jira.py` (SynapseRT; replaced by a team-supplied script + the `references/import-contract.md` convention)
- **Skill English version lags**: this round back-migrated zh_CN in full; `en_US/skills` is still the old version (only superseded items removed and stale references fixed), new / upgraded content will be filled in after B2–B3 are done, with status tracked in the CHANGELOG / skill `en_US` lags behind `zh_CN` and is tracked here
- Next: finish `en_US/skills` i18n and the reviewed-Starter wiring (the `software-development-reviewed` squad and agents' finer-grained mounts)

## v0.0.11 - 2026-09-05 · Internal back-migration batch 1: methodology docs + MULTICA.md

### Added

- `docs/zh_CN/FLOW.md` + `docs/en_US/FLOW.md` — Deliverable-driven flow: work packages enter only when Required; after a Reviewer rejects, verification must be re-run before re-review. Corrects the misconception that "producer roles must appear in sequence"; covers the two-layer loop per deliverable (after a Reviewer rejects, **verification must be re-run** before re-review), dynamic main flow, verification/review sub-loops, sequence diagram, work-package table, three typical trims, and the Leader checklist
- `docs/zh_CN/role-skills-architecture.md` + `docs/en_US/role-skills-architecture.md` — The four-layer skill model (content / orchestration / platform / review) and the "would this change if we changed company" test for layering; includes the role → skill mount matrix and common mistakes
- `docs/zh_CN/test-automation-in-repo.md` + `docs/en_US/test-automation-in-repo.md` — Automation assets in the repo: prose on the team platform, executable scripts in Git, **paths read only from the product repo root `MULTICA.md`**, a missing file means BLOCKED
- `docs/zh_CN/multi-repo-and-issue-links.md` + `docs/en_US/multi-repo-and-issue-links.md` — The repo matrix is the single source of truth (Multica does not detect it automatically); mandatory upstream-read list for linked Issues and how each role reads
- `docs/zh_CN/platform-collaboration.md` + `docs/en_US/platform-collaboration.md` — Platform capability is written exactly once: URL / credentials / REST details exist only in `multica-platform-*`, and role skills only declare "what to read, what to write, whom to call"
- `templates/zh_CN/MULTICA.md` + `templates/en_US/MULTICA.md` — Product repo root context template: layout, test automation paths (one per repo when split), build and verify commands, branch conventions, credentials as **variable names only**

### Changed

- `docs/zh_CN/where-to-put-things.md` + `docs/en_US/where-to-put-things.md`: cheat sheet gains 5 rows (which layer a capability goes in / where platform details go / how to trim the flow / how to route multiple repos / where automation scripts go)
- `README.md` + `README.en.md`: docs table gains five entries: `FLOW`, `role-skills-architecture`, `platform-collaboration`, `test-automation-in-repo`, `multi-repo-and-issue-links`
- `ROADMAP.md`: adds the four-batch "Internal-edition back-migration" plan and four migration red lines
- `AGENTS.md`: structure diagram gains `MULTICA.md` and the new methodology docs; the three-layer model is extended to **four layers** (content / orchestration / platform / review) and the `MULTICA.md` mechanism is explained

### Migration notes

- Back-migrated from the internal fork and **desensitized**: removed internal domains / IPs / domain-account variables (`SHIDAITS_DOMAIN_*` → `ATLASSIAN_USER` / `ATLASSIAN_PASS`), internal system names (BOSS / AngelAlign / SynapseRT / 138 Bridge), and company project name examples (`cds-*` → `acme-*`); internal hosts, account env vars, internal system names and project examples replaced with placeholders
- **Not migrated** (bound to company-internal systems, recorded in the ROADMAP red lines): `multica-design-ui-impl` (BOSS master / AngelAlign spec), `multica-platform-knowledge-base` (138 Bridge), `import_to_jira.py` (SynapseRT); skipped as company-coupled
- **Skill English version lags**: this batch only lands the bilingual `docs/` and root documents; new / upgraded skills are guaranteed in `zh_CN` first, and `en_US` will be filled in after B2–B3 and tracked in this file as pending
- Upcoming batches: B2 adds 9 skills, B3 upgrades existing skills, B4 syncs agents / squads and wraps up

## v0.0.10 - 2026-08-22 · Full-review fixes: consistency & bilingual sync

### Changed

- `bug-fix/squad.md` (zh/en): the team section removes `@Architect` / `@Designer`, consistent with the core design that "bug fixes do not go through the Architect"; affected ends are only frontend / backend, no longer wrongly listing the design end. Bug squad removes Architect & Designer from the team list to match the "no Architect" design
- `bug-fix/squad.md` (zh/en) + `software-development/squad.md` (zh/en): step one / requirement readiness adds guidance for linked Issues to "fetch requirements / scope / acceptance criteria from the external system by `<ISSUE-KEY>` or link", aligned with issue.md's "pick one source". Squad instructions now pull requirements for linked Issues from the external system
- `README.md` / `README.en.md`: the Issue template description changes from "includes Git branch" to "source supports link-type / fully self-contained, pick one" (issue.md already dropped the Git branch chapter in v0.0.9). Root READMEs drop the stale "Git branch" claim
- `en_US/squad/software-development/README.md`: the "Shared Skills" count in the directory table is corrected from the stale 6 to 16, consistent with the body text. en starter README fixes the stale "6 Skills" count
- `software-development/issue.md` (zh/en) + `bug-fix/issue.md` (zh/en): the field list in "why it is written this way" is aligned with the template's actual sections (References / Notes); bug-fix adds a "common failure modes" section, consistent with software-development. Issue "why" sections list the real sections; bug-fix adds a "common failure modes" section
- `agents/devops.md` (zh/en) + `skills/platform/multica-platform-jenkins/SKILL.md` (zh/en): remove references to the deleted Issue "Git branch" block; the deploy branch is now "determined by the Issue source and affected ends; for linked Issues, the external system's branch prevails". DevOps & Jenkins skill drop the stale reference to the removed Issue "Git Branch" block
- `agents/backend-developer.md` (zh/en): "why it works" adds the division of labor "the backend owns the contract; the architect only gives the plan and steps"; and "self-proof" is changed to "self-check evidence", making clear that running `multica-verification` is a self-check and the gating authority rests only with the Leader. Backend Dev doc clarifies the contract-owner split and that self-check ≠ Leader gate

### Why

- The full review found that after many iterations the docs above had leftover count omissions, claims inconsistent with deleted sections, and Squad instructions not wired to the lightweight link-type usage; this round fixes them together so "copy and run" does not hit pitfalls. Full-review sweep fixed leftover counts, stale claims, and Squad instructions lagging behind the lightweight Issue mode

## v0.0.9 - 2026-08-22 · Issue template dual-form: lightweight Jira/Tapd link mode

### Changed

- `software-development/issue.md` (zh/en) adds an "Issue source (required, pick one)" block: supports "external system link (lightweight)" with only link + affected ends + one-line summary, or "fully self-contained" with everything filled in; the "why it is written this way" section at the bottom explains the source split. Issue template adds "Issue source (pick one)" — lightweight external-link mode vs fully self-contained
- `bug-fix/issue.md` (zh/en) gets the same "Issue source (required, pick one)" block. Bug issue template gets the same "Issue source (pick one)" block
- `software-development/README.md` (zh/en) file list and Step 4, and the root `README.md` / `README.en.md` Step 4 description updated to reflect the lightweight link usage. Starter READMEs + root READMEs updated to mention link-style filling
- `software-development/issue.md` (zh/en) fixes role mismatches: the requirement traceability matrix is now marked "left blank when filing, backfilled by the Tester"; technical context becomes optional (the Architect completes it at G1); constraints are split into "business constraints (filled by PM) / engineering constraints (added by Architect)"; verification method is downgraded to "expected verification dimensions (indicative, decided by Leader/Tester)"; the root README flow adds the "requirement convergence (G0)" stage. Issue template fixes role mismatch: matrix is Tester-backfilled, context is optional, constraints split, verification is indicative; root README flow adds G0
- `software-development/issue.md` (zh/en) trimmed further: removes the five chapters "requirement traceability matrix / technical context / constraints / verification method / Git branch", keeping only background / goal / scope (including affected ends) / non-goals / acceptance criteria / source / references / notes, so the template returns to a pure requirement contract. Issue template trimmed: drop matrix/context/constraints/verification/Git-branch; keep requirement-contract sections only

### Why

- Issues come in two real forms: Jira/Tapd links (full requirements live in the external system) and fully self-contained Markdown. The original template defaulted to full and was too heavy for link-type; with the source split, a link-type Issue needs only "link + affected ends + summary" to drive G0 routing and the multica-verification gate, and both forms share the same `<ISSUE-KEY>`. The source selector lightens link-type Issues while keeping gates intact
- The filer is usually a PM (one Issue is one requirement), while the traceability matrix / technical context / engineering constraints / verification method are downstream role artifacts. Making them mandatory for the PM up front leads to invented IDs or stale information; the Issue should be only the requirement contract (why / what / acceptance / non-goals), with the rest backfilled by the Squad during the run. The filer is usually a PM; matrix/context/constraints/verification are downstream artifacts, not requirement inputs

## v0.0.8 - 2026-08-20 · CI/CD gate + Tester three-phase + DevOps role + platform shells

### Added

- New `DevOps` role (`templates/zh_CN/agents/devops.md`): triggers CI/CD after G2 PASS and code push, returns the deploy environment URL, writes no business code. New `DevOps` agent: triggers CI/CD after G2, returns deploy URL, no business code
- Added 5 platform-layer placeholder shell skills (no internal addresses/credentials, placeholders only): `multica-platform-confluence`, `multica-platform-jira`, `multica-platform-jenkins`, `multica-artifact-cicd-sync`, `multica-test-automation`. Added 5 platform-layer shell skills (no internal URLs/credentials, placeholder only)
- New `docs/zh_CN/cicd-and-test-pipeline.md`: G2.5 and Tester T1/T2/T3 methodology, deploy branch model. New `docs/zh_CN/cicd-and-test-pipeline.md` methodology
- `artifact-conventions.md` (zh/en) adds "three-layer architecture: content/orchestration/platform" and the standard usage of the PM/Architect dual skills. `artifact-conventions.md` (zh/en) adds three-layer architecture + dual-skill usage
- Role count 8 → 9 (DevOps added); Skills 11 → 16 (5 platform shells added). Roles 8 → 9 (DevOps); Skills 11 → 16 (5 platform shells)

### Changed

- `gates-and-evidence.md` (zh/en) gate table adds a **G2.5 (CI/CD deploy)** row + walkthrough example. `gates-and-evidence.md` (zh/en) adds **G2.5** row + walkthrough
- `tester.md` (zh/en) upgraded to **T1/T2/T3 three phases** (T1 cases, T2 coverage, T3 post-deploy automation), removing concrete platform bindings. `tester.md` (zh/en) upgraded to T1/T2/T3 three-phase
- `leader.md` (zh/en) routing adds PM-first dispatch, Tester three-phase routing, DevOps/G2.5 routing. `leader.md` (zh/en) routing adds PM-first, Tester three-phase, DevOps/G2.5
- `product-manager.md` (zh/en) gains the dual-skill phrasing "first structure with `multica-pm-requirement-spec`, then land with `multica-pm-artifact-publish`". `product-manager.md` (zh/en) gains dual-skill pattern
- `software-development/squad.md` and `issue.md` (zh/en): stage tables add G2.5 and the deploy branch declaration; the issue template adds a "Git branch" block. Squad & issue add G2.5 + deploy branch
- AGENTS.md structure diagram updated to 9 roles + platform placeholder shells + three-layer model description. AGENTS.md structure updated to 9 roles + platform shells + three-layer model

### Removed

- No real internal addresses/credentials entered the public repo: all platform skills are placeholder shells only, and teams fill in `config.yaml` when integrating. No real internal URLs/credentials enter the public repo; platform skills are placeholder shells only

## v0.0.7 - 2026-08-17 · Artifact platform decoupled into skills

### Added

- Added 5 artifact-sync skills (zh/en, each with a swappable default platform): `multica-pm-artifact-publish` (PRD→Confluence), `multica-design-ui-impl` (UI→Figma), `multica-artifact-architect` (technical design→Git/Confluence), `multica-artifact-backend` (API contract→Apifox), `multica-artifact-test-sync` (cases→local XMind to Jira)
- Rewrote `artifact-conventions.md` (zh/en) into "content spec + sync skill": content belongs to role, platform to skill; no platform name in prompts; to change company, only swap the skill
- `README.md` / `README.en.md` skill tables add the 5 `multica-artifact-*-sync` entries, count 6→11

### Changed

- All 8 agent instructions (zh/en): "WHAT I PRODUCE/OWN/DELIVER" now reads "land via the `multica-artifact-*-sync` skill and return a stable link", dropping the hard-coded `artifacts/<issue-id>/xxx.md` and local platform names (such as the Designer's Figma)
- `templates/zh_CN|en_US/squad/software-development/squad.md`: the stage table and artifact pipeline now say "role returns link via skill", and the [Artifact landing] section becomes [Artifact landing and retrieval], no longer hard-coding local paths

## v0.0.6 - 2026-08-17 · Artifact landing conventions

### Added

- Added `artifact-conventions.md` (zh/en): all stage artifacts land under `artifacts/<issue-id>/` with fixed filenames (PRD=`prd.md`, technical design=`design-tech.md`, UI design=`design-ui.md`, API contract=`api-contract.md`, feature cases=`cases-feature.md`, API cases=`cases-api.md`, test report=`test-report.md`, acceptance=`acceptance.md`); downstream locates by relative path, never writes absolute paths / never leaks the workspace / never relies on search / references must pass the path explicitly / which copy wins in a conflict / artifact changes keep the path and update the content / gates re-judge accordingly / doc table and common mistakes synced
- `where-to-put-things.md` (zh/en) gains a row: where collaboration artifacts go → `artifacts/<issue-id>/` (see artifact-conventions)
- `README.md` / `README.en.md` doc tables add the `artifact-conventions` entry

### Changed

- `templates/zh_CN|en_US/squad/software-development/squad.md`: the stage table and artifact pipeline annotate each artifact's landing path; added an [Artifact landing] rule requiring the Leader to give the artifact path explicitly when dispatching
- Every agent instruction (zh/en) "WHAT I PRODUCE/OWN/DELIVER" now states its artifact landing path and a hard instruction to "read upstream `artifacts/<issue-id>/...`", so downstream roles locate upstream artifacts accordingly

## v0.0.5 - 2026-08-17 · Add ProductManager role + AI-readable requirement discipline

### Added

- New `ProductManager` agent instructions (`templates/zh_CN|en_US/agents/product-manager.md`): turns ideas / asks / meeting notes into PRDs that can be reviewed, designed, developed and tested (with G-/FR-/BR-/AC-/KPI-/RISK-/OP- numbering, alignment to six reader types, requirement type → artifact form, AI-readable discipline, collaboration preferences)
- The role vocabulary now includes `ProductManager`, and item 2 of `naming-conventions.md` (zh/en) is synced
- The software-development Starter wires in the PM: the team section adds @ProductManager, the stage table adds S0 requirement output @ProductManager → G0 scope confirmation (based on the PRD), and the artifact pipeline adds step 0; without a PM, the Issue is treated directly as the ready scope and S0 is skipped
- `gates-and-evidence.md` (zh/en) adds "AI-readable discipline for requirement / design artifacts": stable headings, stable table fields, rule numbering, TBDs collected in one place (OP- not closed does not enter development), cross-links between documents, naming the authority in conflicts, no vague words, rules written as text; violating any one makes G0/G1 REJECTED
- Starter role count 7 → 8 (`templates/zh_CN|en_US/squad/software-development/README.md`)

### Changed

- @Designer / @Architect (zh/en): the "product requirements" source now primarily uses the @ProductManager's PRD (falling back to the Issue / @Architect description without a PM), and it is made explicit that product scope / business rules / field definitions belong to the PM, or to Leader convergence without a PM

## v0.0.4 - 2026-08-17 · Three-segment naming (role + project + member-id)

### Changed

- Naming convention upgraded from "role + instance" to "role + project + member-id" `<role>-<project>-<member-id>` to resolve the "real name vs role name" collision: same project + same role + multiple people are disambiguated by the member-id (employee number / nickname, never a full real name)
- Role-prefix wildcard resolution extended to three segments: `@role` → orchestrator dispatches an exact @mention `@role-<squad suffix>-<squad member>` (suffix corresponds to the `<project>` segment, member to the `<member-id>` segment)
- Synced the prefix resolution section / exact dispatch description in `docs/zh_CN|en_US/naming-conventions.md`, `templates/zh_CN|en_US/squad/{software-development,bug-fix}/squad.md` and `templates/zh_CN|en_US/agents/leader.md`, plus all references in README (zh/en), AGENTS.md, adapt-and-scale.md (zh/en), and each squad README's naming heading

### Removed

- Did not adopt the "private squad Profile" mechanism (deemed too complex by the user, not introduced)

## v0.0.3 - 2026-08-17 · Squad instructions re-leveled to Squad scope

### Changed

- Re-leveled the Squad instructions to true squad scope (`templates/zh_CN/squad/software-development/squad.md` and `templates/en_US/...`, and `templates/zh_CN/squad/bug-fix/squad.md` and `templates/en_US/...`): the opening now defines the Squad goal, fact-source & TBD policy, numbering convention (G-/U-/FR-/BR-/AC-/KPI-/OP-/RISK-, software-development), communication style, and prohibited list (software-development), valid for every role; the former "you are the Leader" content moved into a standalone `[Leader Role]` section stating the Leader only orchestrates and holds advancing/gating authority. Borrowed generic patterns but dropped any binding to specific projects, toolchains, or agent names to stay copy-paste-ready

### Added (follow-up: gate discipline enhancements)

- Added three gate disciplines to the Squad-level rules (both zh_CN and en_US squad.md): (1) an in-scope artifact judged N/A must be marked explicitly with reason + Leader confirmation — never silently skipped; (2) once any artifact is modified its downstream gates are invalidated and must be re-judged, never carry over an old PASS (not just implementation — design / API contract / case changes also invalidate downstream); (3) the same artifact failing the gate 3 times in a row escalates to Human instead of endless rework
- Synced `gates-and-evidence.md` (extended gate-invalidation principle to upstream changes and non-silent N/A) and `common-mistakes.md` (new pitfall #9 on silently skipping in-scope artifacts as N/A, plus expanded diagnostic checklist) in both `docs/zh_CN` and `docs/en_US`

### Added (follow-up: borrowed enhancements)

- **Role-prefix wildcard resolution** (solves "how to pin this squad's agent among multiple same-role instances in a workspace"): added "Squad instance suffix & prefix wildcard" to `docs/zh_CN|en_US/naming-conventions.md` — Squad instructions write only the role prefix, the squad declares a suffix at startup, and the orchestrator dispatches `@role-<squad suffix>`; also added a "role prefix resolution" section and precise-dispatch rule to both `squad.md` (zh_CN/en_US) and `agents/leader.md` (zh_CN/en_US)
- **Four verdict values, join gates, gatekeeper-doesn't-edit** added to `docs/zh_CN|en_US/gates-and-evidence.md`: APPROVED / APPROVED_NA / REJECTED / BLOCKED (APPROVED_NA's different downstream is stated by the Leader); join gates require every parallel branch PASS; the gatekeeper only gives a verdict + fix list and never edits the artifact
- **Stage-gate map** added atop `templates/zh_CN|en_US/squad/software-development/squad.md`: a S0–G4 pipeline overview using `@role` placeholders (no hardcoded counts/names), skipping the line for any missing layer
- **Requirements traceability matrix** added to `templates/zh_CN|en_US/squad/software-development/issue.md`: suggested REQ → DESIGN → API → CODE → CASE → TEST mapping to prevent broken links
- **Gatekeeper-doesn't-edit** also synced into the advance rules of both squad.md (zh_CN/en_US, software-development + bug-fix) and leader.md rule #9 (zh_CN/en_US)

### Added (follow-up: new Designer role)

- Added a **Designer** role for UI / interaction design working with Figma, separated from `Architect` (technical design); new `templates/zh_CN|en_US/agents/designer.md`
- `docs/zh_CN|en_US/naming-conventions.md` role vocabulary now includes `Designer`, noting Architect ≠ Designer
- Both `squad.md` (zh_CN/en_US) gained `@Designer` in the team section; software-development's stage-gate map splits into S1a technical design (@Architect) / S1b UI design (@Designer) with @FrontendDev depending on both; bug-fix team section also lists @Designer
- `frontend-developer.md` (zh_CN/en_US) now names @Designer's Figma output as the UI source, falling back to a design doc or mock when absent
- Synced role counts in README / README.en / ROADMAP / AGENTS.md / software-development README (6→7 roles, or 5→6 agents)

## v0.0.2 - 2026-08-16 · Template correctness fixes

### Changed

- Fixed the CI gate templates so the structured verdict emits the actual PASS / FAIL value and the branch-protection script no longer produces a truncated request body
- Fixed Squad routing so Bug Fix dispatches the Tester and API test cases advance in parallel with implementation
- Synchronized the Skill count in the roadmap and clarified that team-level approval requires CODEOWNERS or GitHub Rulesets
- Aligned the project-positioning language with the real-task validation status in the ROADMAP

## v0.0.1 - 2026-08-15 · Initial release

Historical iterations (0.1.0–0.14.0) are condensed into this release: a copy-paste-ready Multica template library.

### Added

- **Agent templates**: 6 shared roles (Leader / Architect / FrontendDev / BackendDev / Tester / Reviewer), located in `templates/zh_CN/agents/` and `templates/en_US/agents/`
- **Skill templates**: 6 shared Skills (`multica-verification` gating / `multica-gate-setup` CI hard gates / `multica-test-design` / `multica-pm-requirement-spec` / `multica-technical-design` / `multica-implementation`), with the unified `multica-` prefix, mounted by name
- **Squad starters**: `software-development` (recommended) and `bug-fix` (experimental), each with a README / squad / issue trio
- **Methodology**: 5 docs in `docs/` (instruction ownership / gates and evidence / common mistakes / trimming and extension / naming conventions)
- **CI hard gates**: `delivery-gate.yml` / `branch-protection.json` / `apply-branch-protection.sh` are self-contained in the `multica-gate-setup` skill
- **i18n**: `README.md` ↔ `README.en.md` link to each other at the top as a switcher; `templates/` and `docs/` are stored in separate `zh_CN/` / `en_US/` directories; root documents (AGENTS / CHANGELOG / ROADMAP / SECURITY / CONTRIBUTING) are single files written Chinese-first with English alongside

### Changed

- None (this is the initial version after the condensed merge). No changes — this is the initial condensed release.
