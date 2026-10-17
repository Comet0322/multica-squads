# Squad benchmark

Goal: tell whether the dev-team squad handles complex work reliably, and which config change helps.

- `rubric.json` — success definition, headline metrics and what is recorded per run (single source of truth). No composite score: reliability (pass^n over repeated runs) comes first, then cost and rework.
- `tasks/` — fixed task texts, T1 (greenfield baseline) to T5 (ambiguous requirement). Only T2 is written so far.
- `hidden/<task>/` — acceptance tests the agents never see (copied into the branch only at scoring time). Not written yet.
- `score.py` — records ONE run: `bench/score.py <PARENT-ISSUE> --task T2 --variant <name> --attempt <1..3> --repo <local clone> --branch <feature branch> --hidden bench/hidden/T2 --config-sha <squads repo sha>`; appends to `results.csv`.
- `report.py [--task T2]` — per (task, variant): successes, pass^n (all runs succeed), pass@n (any succeeds), mean interventions / rework / leader wakeups / minutes / tokens.

## Method
1. Run the task through the squad (chat with sq-lead, text from `tasks/`). Do not intervene; every human status change or comment on the issues counts as an intervention.
2. Run `score.py`; fill the manual items yourself.
3. Run each variant up to 3 times (hard cap, to bound cost) on a fresh copy of the starting repo/branch. A single run is noise.
4. `report.py`; compare variants on pass^n first. Change ONE thing between variants.
A run succeeds only if hidden tests all pass, existing tests green, build/vet/gofmt clean, zero human interventions, and no sub-issue stalled.

## Known limits of the numbers
- `wall_minutes` includes time spent waiting for the human PR merge.
- `tokens` = input + output only (cache tokens excluded).
- "Intervention" = a member-authored status change or comment on the run's issues. The requirement chat is not counted.
