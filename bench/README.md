# Squad benchmark

Goal: tell whether the dev-team squad handles complex work reliably, and which config change helps.

- `rubric.json` — scoring items and weights (single source of truth). 100 points: quality 40, autonomy 30, human rating 30. Efficiency numbers are recorded, not scored.
- `tasks/` — fixed task texts, T1 (greenfield baseline) to T5 (ambiguous requirement). Only T2 is written so far.
- `hidden/<task>/` — acceptance tests the agents never see (copied into the branch only at scoring time). Not written yet.
- `score.py` — `bench/score.py <PARENT-ISSUE> --task T2 --repo <local clone> --branch <feature branch> [--hidden bench/hidden/T2] --config-sha <squads repo sha>`; appends to `results.csv`.

## Method
1. Run the task through the squad (chat with sq-lead, text from `tasks/`). Do not intervene; every human status change or comment on the issues counts as an intervention.
2. Run `score.py`; fill the manual items yourself.
3. Change ONE thing in the config, rerun the same task, compare. Run each variant 2-3 times; a single run is noise.

## Known limits of the numbers
- `wall_minutes` includes time spent waiting for the human PR merge.
- `tokens` = input + output only (cache tokens excluded).
- "Intervention" = a member-authored status change or comment on the run's issues. The requirement chat is not counted.
