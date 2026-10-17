# multica-squads — what this project is

Config-as-code plus experiments for **Multica agent squads** on a self-hosted Multica (docker, `http://localhost:13654`, API `:18734`).
Question being answered: **can an agent squad reliably deliver complex software, and how should it be designed?**
Everything here is pushed to Multica with `./sync.py`; Multica itself is the upstream repo at `/mnt/a0df7f69-337a-4cb4-a10a-f48243e3ddfc/Code/multica` (do not put this config there).

## Layout
- `agents/<n>.json|.md` — agent config (`tier` → `tiers.json`) + instructions. `skills/<n>/SKILL.md`, `mcp/`, `squads/`, `autopilots/`.
- `tiers.json` — model tiers: judgment (Opus 5.5 high: lead, reviewer), execution (Sonnet 5.5 medium: implementer, qa), light (Haiku 5.5: doc, watcher).
- `sync.py [--dry-run] [--workspace X] [--only skills,mcp,agents,squads,autopilots]` — idempotent upsert by name, never deletes. Targets in `workspaces.json`; skips workspaces where you are not admin/owner.
- `tools/chat.py <agent> "<msg>" [--session ID]` — Multica CLI cannot send chat; this uses the REST API with the token in `~/.multica/config.json`.
- `tools/forgejo-pr.sh` — opens a PR on the local Forgejo (token from `forgejo/.env`).
- `forgejo/` — local Forgejo compose (UI `http://localhost:13000`, user `squadadmin`; secrets in gitignored `.env`, `.connection.json`).
- `bench/` — rubric, tasks, per-run scorer, aggregate report (see `bench/README.md`). Reliability metric is pass^n over at most 3 runs per variant (user cap), following tau-bench; no composite score.

## Current squad (`dev-team`, config v6)
Leader `sq-lead` + `sq-implementer`, `sq-reviewer`, `sq-qa`, `sq-doc`; utilities `sq-medic` (autopilot `squad-medic`, every 5 min: restarts runs that stopped by accident, relays human PR comments onto the spec issue) and `sq-watcher` (autopilot `pr-watch`, GitHub only). **Both autopilots are currently `paused`**; unpause `squad-medic` before probes or scored runs (`multica autopilot update <id> --status active`).
Vocabulary is in `GLOSSARY.md` (scenario vs task, scope tiers A/B/C/D, scored run vs deterministic probe, intervention vs recovery). v6 scope: A (scored) = feature-add + symptom bug; B (mechanism, verified once) = greenfield, PR-comment relay, fast path; C (must be refused in chat) = 12 scenarios incl. UI, performance, migrations, multi-repo, hotfix; D (measured only) = context peaks.
Flow: user chats with sq-lead → lead checks the **capability boundary** and refuses out-of-scope work in chat without creating issues → spec + ticket plan approved in chat → spec issue (frozen) with a stage-1 `spec-check` handoff (sq-reviewer: ACs testable, Impact-analysis files exist, a bug's Reproduction actually reproduces) → feature tickets F1..Fn in stages, each implement → review → QA → final `Deliver` ticket: integration QA (full suite + every AC of the whole spec, pasted output) → docs → open PR → spec `in_review` at the PR (the only human gate) → user merges → Forgejo webhook sets the spec `done` (PR body must contain `Closes <SPEC-ID>`). A change tiny by all four tests may run the fast path (implement → review → PR) after the user says yes.
Every issue the lead creates gets label `run-<YYYYMMDD>-<slug>` so runs can be filtered.

## Hard-won facts (verified unless marked)
- Squad assignment/@mention wakes **only the leader**; members run only when assigned/@mentioned. Squad `instructions` go to the leader only. `role` is a roster label.
- **Platform default says delivered → `in_review`, `done` stays human.** Stage barriers only fire on `done`/`cancelled`. Agent instructions outrank the platform workflow ("Instruction Precedence"), but a *skill* does not, so the status override lives in each agent's own `.md`. Leader also self-heals sub-issues stuck in `in_review`.
- Chat (leader) sees repos only if registered: `multica repo add <url>`; then `multica repo checkout <url>` gives a worktree. Daemon clones need credentials (`~/.git-credentials` has the Forgejo entry). Workspace repo list: kv-cli on Forgejo.
- Forgejo reachable by Multica backend as `http://forgejo:3000` (shared docker network `multica_default`); webhook target must be `http://backend:8080/api/webhooks/vcs/<connection-id>`, not the localhost URL the UI shows. Forgejo needs `webhook.ALLOWED_HOST_LIST=*`.
- Timeline entries carry `actor_type` (agent/member) → interventions are measurable; runs carry `usage` (array per model), `is_leader_task`.
- **`attribution.source` is NOT "who started this run"** — it names the human or agent at the root of the causal chain, so it is useless on its own (measured table in `bench/failures.md`). A platform stage barrier reports `delegation` in an agent-built family but `direct_human` in a hand-built one; a person firing a rule by hand reports **`trigger_owner`**. What actually discriminates: `wakeup_system_rule` non-null = a platform rule fired; `attribution.delegated_from_task_id` present = another agent's task caused it; neither = a person (or an `sq-medic` restart, which the scorer pairs with its `**Medic**` comment). `usage` entries also carry `cache_read_tokens`/`cache_write_tokens`; one v4 leader run peaked at **1.23M** cache reads.
- **Platform stage barriers are reliable; v4's missed wake was not a barrier.** Setting a child `done` fires `child_done` on the parent within ~20 s, and `issue update --no-start` suppresses the run on the issue being updated but **not** the parent's barrier. v4's un-woken leader came from an **agent-created** wakeup rule that the platform rate-paused; v6 creates no such rules (v5 families have zero and their barriers fired).
- **A comment on a squad-assigned issue wakes the leader by itself**, so commenting and then `rerun`-ing the same issue wakes it twice, 30 s apart — two leaders on the same state can promote a stage or open a rework twice (found by probe F17-2, fixed in `agents/medic.md`).
- `multica issue wakeup create` needs an explicit `--agent-id` when a person runs it (it defaults to the authenticated *agent*), and event names are dotted (`comment.created`, not `issue_commented`); `multica issue wakeup events` lists them.
- `multica issue runs <id> --active` answers "is an agent working right now", `--siblings` widens it to the issue family. `multica issue rerun <id>` re-enqueues the current assignment and does not depend on wakeup rules (what sq-medic uses); `multica issue wakeup trigger` is the manual fire, and `manual` fires bypass the rate pause (`issue_wakeup.go:1292`).
- The VCS webhook models only `pull_request` and `ci_status` (`vcs_webhook.go:139`); **PR comments never reach Multica through it**, so the PR-comment relay polls the Forgejo API instead (`tools/forgejo-pr-comments.sh`). CI status *is* modelled, so Forgejo Actions would mirror onto the PR without extra wiring.
- Agents push as **`squadbot`** (credential in `~/.git-credentials`, token also in `forgejo/.env` as `FORGEJO_TOKEN`; the admin token is kept as `FORGEJO_ADMIN_TOKEN`). `main` is protected on `kv-cli` and `kv-bugs`: direct push is rejected by the server and only `squadadmin` may merge. Verified for real, not by reading settings.

## Experiment log
1. hello CLI — needed many manual DONE clicks (status policy bug). 2. hello CLI — one nudge to wake the lead. 3. todo CLI + PR on GitHub — zero intervention to PR; merge needed manual status. 4. kv CLI + PR on Forgejo — zero intervention, merge auto-set `done`.
All four are tiny greenfield tasks: they prove the pipeline, **not** that complex work is reliable.

## Open items / next
- Repo-checkout workflow (lead reads repo before spec; members use `multica repo checkout`, push feature branch) is written into instructions but **untested** — first test: T2 on kv-cli. Unverified: push from a checkout worktree to Forgejo; later stages fetching the earlier branch.
- Scored A-layer tasks: **T3** (kv-bugs symptom bug, hidden tests in `bench/hidden/T3`) and **T2-hard** (`bench/tasks/T2-hard-store-format-v2.md`, hidden tests in `bench/hidden/T2-hard`), both validated and **user-approved 2026-10-17**. T2 (export/import) is retired from the scored layer: too easy. T1, T4, T5 not written.
- PRs are currently opened by the shared admin account `squadadmin`; plan: separate bot account + main-branch protection so human review is real.
- PR body should cite concrete sub-issue ids/verdicts (run 4 body was vague).
- Possibly simplify to lead + implementer + reviewer (more roles = more lossy handoffs); decide from benchmark data, not intuition.
- `pr-watch` autopilot only matters for GitHub PRs; pause it when not needed (`multica autopilot update <id> --status paused`).

## Rules for working here
- Benchmark runs: never delete feature branches/PRs/issues/labels; one branch per attempt, PRs left open (not merged), `main` untouched.
- Run the squad hands-off when testing; never press status buttons mid-run (it invalidates the run).
- Commit after each config change; scorer records the squads-repo sha.
- Confirm with the user before outward-facing actions (creating repos, pushing to remotes, spending lots of agent runs).

## Benchmark results log
- T2 / v1 (config 8f1289f): 3/3 success, pass^3 true, 0 interventions, 0 rework. Task too easy to exercise review/QA loops (caveats in bench/README.md).
- T3 added (repo `kv-bugs`, tag `bench-base-t3`, hidden tests `bench/hidden/T3`): three symptom reports incl. concurrent lost updates; baseline fails 4 hidden tests, reference fix passes.
- v2 (9269ad1): spec/internal labels, single Status comment on parent. v3: numbered AC, ticket `Spec:`/`Covers:` lines, per-AC tables from reviewer/QA, parent description frozen after agreement, members mention only the leader.
- v4: chat output = spec + feature breakdown plan, user approves both; one spec -> several feature tickets (vertical slices); each feature gets its own implement/review/QA stages in sequence on one branch; docs and PR once at the end. Handoff issues are hidden from humans by `internal` label filter, not by reducing their number.
- v5 (written, NOT yet synced until v4 run ACHE-75 finishes): three issue levels spec -> ticket (feature) -> handoff. Spec issue frozen, tickets are its staged sub-issues, handoffs are the tickets' sub-issues (nesting + barrier wake verified on ACHE-93..96). Reason: platform pauses the child_done wake after 12 triggers per issue (seen on ACHE-75); per-ticket handoffs keep each issue far below it.
- T3 / v4 attempt 1 (ACHE-75, config fa404d8): code correct (hidden 100%, existing green, build clean) but success=0 because 2 human interventions were needed: platform paused the child_done wake after 12 triggers (wakeup_paused, 07:27) and the leader was not re-woken after the PR stage. 15 leader wakeups, 4 rework issues (ACHE-87..92), 32.6 min. 2 of 3 v4 attempts remain; plan is v5 instead.
- v5 attempt 1 (spec ACHE-97, tickets ACHE-98..101) was STOPPED by the user after F1 finished (ACHE-101 done, 102-104 done); ACHE-98 run cancelled. Not scored. The whole family (ACHE-97..100) was set `cancelled` on 2026-10-17 with `--no-start` so the v6 `squad-medic` autopilot cannot restart it; nothing was deleted. Handoff with the open design problems: /tmp/multica-squads-handoff.md
