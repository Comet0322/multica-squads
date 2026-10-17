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

## Current squad (`dev-team`)
Leader `sq-lead` + `sq-implementer`, `sq-reviewer`, `sq-qa`, `sq-doc`; utility `sq-watcher` (autopilot `pr-watch`, every 5 min, closes `in_review` issues whose **GitHub** PR merged).
Flow: user chats with sq-lead (needs, architecture) → lead writes spec into a parent issue assigned to the squad + staged sub-issues (1 implement, 2 review, 3 QA, 4 docs, 5 open PR) → members finish and set their own sub-issue `done` → stage barrier wakes lead → lead promotes next stage / creates rework → parent `in_review` at the PR (the only human gate) → user merges → Forgejo webhook sets parent `done` (PR body must contain `Closes <PARENT-ID>`).
Every issue the lead creates gets label `run-<YYYYMMDD>-<slug>` so runs can be filtered.

## Hard-won facts (verified unless marked)
- Squad assignment/@mention wakes **only the leader**; members run only when assigned/@mentioned. Squad `instructions` go to the leader only. `role` is a roster label.
- **Platform default says delivered → `in_review`, `done` stays human.** Stage barriers only fire on `done`/`cancelled`. Agent instructions outrank the platform workflow ("Instruction Precedence"), but a *skill* does not, so the status override lives in each agent's own `.md`. Leader also self-heals sub-issues stuck in `in_review`.
- Chat (leader) sees repos only if registered: `multica repo add <url>`; then `multica repo checkout <url>` gives a worktree. Daemon clones need credentials (`~/.git-credentials` has the Forgejo entry). Workspace repo list: kv-cli on Forgejo.
- Forgejo reachable by Multica backend as `http://forgejo:3000` (shared docker network `multica_default`); webhook target must be `http://backend:8080/api/webhooks/vcs/<connection-id>`, not the localhost URL the UI shows. Forgejo needs `webhook.ALLOWED_HOST_LIST=*`.
- Timeline entries carry `actor_type` (agent/member) → interventions are measurable; runs carry `usage` (array per model), `is_leader_task`.

## Experiment log
1. hello CLI — needed many manual DONE clicks (status policy bug). 2. hello CLI — one nudge to wake the lead. 3. todo CLI + PR on GitHub — zero intervention to PR; merge needed manual status. 4. kv CLI + PR on Forgejo — zero intervention, merge auto-set `done`.
All four are tiny greenfield tasks: they prove the pipeline, **not** that complex work is reliable.

## Open items / next
- Repo-checkout workflow (lead reads repo before spec; members use `multica repo checkout`, push feature branch) is written into instructions but **untested** — first test: T2 on kv-cli. Unverified: push from a checkout worktree to Forgejo; later stages fetching the earlier branch.
- T2 hidden tests written and validated (`bench/hidden/T2`); T1, T3-T5 task texts and tests not yet written; user must approve tasks before scored runs.
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
