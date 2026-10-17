# Squad benchmark

Goal: tell whether the dev-team squad handles work reliably *within its declared
scope*, and which design change helps. Vocabulary (scenario, task, scope tier,
scored run, deterministic probe, intervention vs recovery) is defined in
`../GLOSSARY.md`.

- `rubric.json` — success definition, budget, headline metrics, and the rule for
  claiming an improvement (single source of truth).
- `tasks/` — fixed task texts. A layer (scored) for v6: `T3` (bug from symptoms)
  and `T2-hard`. `T2` is kept but no longer scored: 3/3 with zero rework made it
  too easy to exercise review or QA.
- `hidden/<task>/` — acceptance tests the agents never see, copied into the branch
  only at scoring time.
- `probes/` + `probes.csv` — deterministic probes: the capability-boundary refusal
  prompts, the fault-injection cases, and the one-off mechanism checks.
- `failures.md` — the failure-mode ledger.
- `score.py` — records ONE run: `bench/score.py <PARENT-ISSUE> --task T3 --variant <name> --attempt <1..3> --repo <local clone> --branch <feature branch> --hidden bench/hidden/T3 --config-sha <squads repo sha>`; appends to `results.csv` and writes `runs/<parent>.json` (per-agent usage and attribution).
- `report.py [--task T3]` — per (task, variant): successes, pass^n, pass@n, mean interventions / rework / leader wakeups / minutes / tokens.
- `watch.py` — status/timeline watcher for a run in flight.

## Method
1. Run the task through the squad (chat with sq-lead, text from `tasks/`). Do not
   intervene; every human status change, comment or hand-started wake counts.
2. Run `score.py`; fill the manual items yourself.
3. Up to 3 runs per variant per task (hard cap), on a fresh copy of the starting
   repo/branch. A single run is noise. At most 12 scored runs per version.
4. `report.py`; compare on pass^n first, then cost and rework.
5. Classify every failure in `failures.md` and point it at the change it caused.

A run succeeds only if hidden tests all pass, existing tests are green,
build/vet/gofmt are clean, human interventions are zero, automated recoveries are
within the cap, and no sub-issue stalled.

### One change at a time — and where that rule does not apply
"Change ONE thing between variants" applies to prompt and flow changes that move
the pass rate, compared with scored runs. It does **not** apply to mechanism
changes (recovery agent, branch protection, CI, a new handoff stage): with 3 runs
per variant, pass^n cannot resolve which of four mechanisms helped, so isolating
them by scored runs would spend the whole budget for no signal. Mechanisms ship as
one bundle and are each proven by their own deterministic probe.

## Known limits of the numbers
- `wall_minutes` includes time spent waiting for the human PR merge.
- `tokens` = input + output only; cache reads are reported separately as
  `peak_cache_read_tokens` (one v4 leader run peaked at 1.23M).
- 3/3 means "no instability seen in three runs", never a probability: the 95%
  lower bound is about 0.37 (rule of three). Improvement claims follow
  `improvement_claim_rule` in `rubric.json`.
- Rows scored before v6 used a weaker intervention definition that could miss a
  hand-started wake (see `failures.md`). Do not compare them as if identical.

## Records are never deleted
Every attempt keeps its own feature branch (`feat/<task>-<variant>-a<N>`), open PR
(not merged), parent/sub-issues and run label. `main` and the task's baseline tag
stay untouched, so attempts are independent and all evidence stays available.
