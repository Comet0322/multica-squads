# Handoff: Multica agent-squad design — open problems to resolve

Written for a fresh, stronger agent. The user (Traditional Chinese speaker) wants to design agent squads that deliver software reliably with humans only reviewing and merging. Reply to them in Traditional Chinese.

## Read first
- `/home/comet/Code/multica-squads/CLAUDE.md` — project context, layout, verified facts, experiment log (do not duplicate it here).
- `agents/lead.md` (current design = v5), `squads/dev-team.md`, `skills/*/SKILL.md`, `bench/README.md`, `bench/tasks/T2*.md`, `T3*.md`, `bench/results.csv`.
- Git repo `/home/comet/Code/multica-squads`, commits use `-c user.name=Comet0322 -c user.email=jerrymark611@gmail.com`; end commit messages with the Co-Authored-By line from the session attribution.

## Where things stand
- Config v5 (spec issue -> ticket issues (one feature each) -> handoff issues (implement/review/QA, then docs/PR in a Deliver ticket)) is synced to Multica (`python3 sync.py`). Only F1 of one run has executed (spec ACHE-97; tickets ACHE-98/99/100/101; F1 handoffs ACHE-102..104). The run was stopped by the user; ACHE-98 run cancelled. Nothing deleted.
- Scored results: T2/v1 3/3 pass; T3/v1 3/3 pass (reworks occurred in 2 of 3); T3/v4 attempt 1: code correct (hidden 100%) but success=0 because 2 human interventions were needed. See CLAUDE.md.
- Benchmark: `bench/run_attempts.py` (v1-style one-shot driver; does NOT yet support the v5 two-step chat approval), `bench/score.py`, `bench/report.py`, `bench/watch.py` (reliable status/timeline watcher), hidden tests in `bench/hidden/T2|T3`. Rules: max 3 runs per variant, pass^n headline, never delete branches/PRs/issues/labels.
- Repos: Forgejo local (`squadadmin/kv-cli`, `squadadmin/kv-bugs`, baseline tags `bench-base-t2`, `bench-base-t3`); credentials live in `forgejo/.env` (never print).

## Facts verified the hard way (use them)
- Platform auto-wake rule `child_done` is an event rule; the platform pauses it when it has started >= 12 runs in the past hour (`wakeupHourlyRunLimit = 12`, reason `rate`, activity `wakeup_paused`). It does NOT auto-resume; a person's manual "wake now"/comment is exempt and resumes work. Source: upstream `server/internal/service/issue_wakeup.go` + `issue_wakeup_activity.go`. The local checkout of multica is older than the running image; use the read-only remote `upstream-ro` (https://github.com/multica-ai/multica.git) in `/mnt/a0df7f69-337a-4cb4-a10a-f48243e3ddfc/Code/multica` (fetched main 18fa9f728).
- Nesting spec -> ticket -> handoff works to 4 levels; completing a child wakes the parent's assignee at every level (tested with ACHE-93..96, `[nesting-test]` issues, left in place).
- `multica issue list` pages at 50 by default (use `--limit 100 --offset`); `multica issue children` has NO json output; `multica auth status` prints to stderr; chat is sent via REST (`tools/chat.py`), the CLI chat is read-only; `cancel-task` takes a run id only.
- Squad assignment wakes only the leader; members run only when assigned/mentioned; stage barriers wake the parent's assignee only when the lowest unfinished stage is all done/cancelled (not in_review). Agent's own instructions outrank platform workflow text, skills do not.
- Leader wakeups cost: each wake reloads 250-800k cached input tokens; v4 total ~152k non-cache tokens vs v1 ~67k.
- Counting `rework` in score.py is by "rework" in sub-issue title; earlier "review verdict" keyword counters are unreliable.

## Open problems to resolve (user asked to record them)
Scenario analysis of the current design; "tested" = actually run, otherwise inferred from instructions only.

| # | Scenario | Status / gap |
|---|---|---|
| 1 | Empty-repo new project | informal only; architecture decisions unreviewed by anyone but the user |
| 2 | Add feature to existing repo | T2 3/3, but too easy (no rework) |
| 3 | Bug with clear symptoms | T3 passes; root cause diagnosed by leader alone, nobody verifies the diagnosis |
| 4 | Unknown-root-cause / intermittent bug | no investigation ticket type, no fallback if not diagnosable |
| 5 | Wide mechanical refactor | vertical slices don't fit; needs expand/contract sequencing |
| 6 | Vague requirements | untested; no "enough questions asked" criterion |
| 7 | Multi-repo | assumes one spec = one branch = one PR |
| 8 | Tiny change (typo, doc) | same heavy 8-10 issue flow; needs a fast path (assign straight to implementer) |
| 9 | Urgent hotfix | approval gate in chat slows it; no reduced flow |
| 10 | Requirement changes mid-run | spec frozen, one-line rule only; in-flight/finished tickets undefined |
| 11 | UI / visual work | QA cannot see UI; no browser/screenshot tooling |
| 12 | Performance / non-functional | no measurement tooling or baselines for QA |
| 13 | DB migration / deploy / irreversible ops | only gate is the final PR; no risk classification |
| 14 | PR review feedback from human | no loop back from Forgejo comments to the squad |
| 15 | main moves during the run | no rebase/realign step |
| 16 | Several specs concurrently | conflicts found only at merge |
| 17 | Stuck / platform throttled | PROVEN failure in v4 (wakeup_paused, leader never re-woken, twice); no watchdog, no resume |
| 18 | Repo without tests | no "establish test baseline" ticket type |
| 19 | Security / permissions | rules (no merge, no commit to main, spec frozen, status override) enforced only by prompt; shared Forgejo account, no branch protection, no bot account |
| 20 | Long tasks / context size | never measured per-role context peaks |

Cross-cutting gaps, most severe first:
1. No explicit owner of integration verification: 3 tickets -> one PR; only the leader's own check (unverified that it runs the full suite). Candidate fixes: final "integration QA" handoff in the Deliver ticket (full tests incl. `go vet`, `-race`, ALL ACs) and Forgejo CI on the PR (needs a runner; feasibility unchecked).
2. Guarantees are prompts, not mechanisms (branch protection, CI, permission isolation, bot account).
3. Spec correctness is unreviewed (leader writes spec and diagnoses root cause; reviewer/QA only check implementation vs spec). Consider an independent spec/diagnosis review step before approval.
4. No watchdog/recovery for stuck runs or paused wakeups (candidate: scheduled autopilot or script that detects idle specs and re-wakes the leader; remember a member comment counts as human intervention in the benchmark, so a bot should be a separate, labeled actor).
5. No flow tiers (tiny change vs normal vs high-risk).
6. Human feedback loop is one-ended (chat in, merge out; nothing for mid-run changes or PR comments).
7. Evaluation too narrow (one tiny Go CLI, 3 runs; none for UI, multi-repo, vague reqs, refactor).
8. Cost opacity: no budget cap; leader wakeups dominate cache reads.
9. Reviewer/implementer share model family; real reviewer catches only evidenced in T3 reworks.
Smaller known items: v5 created ticket F1 last (ACHE-101 after 98-100) — cause unchecked; leader plays two levels (spec/ticket) distinguished only by labels (one sample); PR author still the shared `squadadmin` account; `pr-watch` autopilot only matters for GitHub PRs; manual 1-5 scores in results.csv unfilled.

## What the user cares about (preferences)
- Humans should only see the spec issue (label `spec`) and the final PR; handoff issues are noise they want hidden, not necessarily fewer.
- Autonomy rule: `blocked` only if truly unsolvable, `in_review` only for explicitly declared human gates, everything else automatic and never wait for the user to press buttons.
- Never delete benchmark branches/PRs/issues/labels. Do not merge benchmark PRs.
- At most 3 runs per variant; be honest that 3 passes only means "no instability seen".
- They ask for plain explanations; do not hide uncertainty; say what was tested versus inferred.
- Don't change synced config in the middle of a run (it mixes versions).

## Suggested skills for the next agent
- `mattpocock-skills:grill-with-docs` (or `grilling`) to settle priorities with the user before changing the design.
- `mattpocock-skills:to-spec` / `to-tickets` only as inspiration: user wanted spec and ticket as distinct artifacts; their vertical-slice, blocking-edge, "fits one context window" ideas were discussed (note: to-spec forbids file paths, our Impact analysis requires them).
- `mattpocock-skills:diagnosing-bugs` and `code-review` for evaluating failed runs and PR quality.
- `mattpocock-skills:wayfinder` is probably overkill; `retro` fits after the next run.
