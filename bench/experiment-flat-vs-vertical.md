# Experiment plan: who grills, and how many roles (draft, 2026-11-23)

Nothing here has been run. Two questions, kept separate because they were conflated before.

1. **Where does requirement clarification happen?** (mattpocock expects `/grill-with-docs` with a human, then `ready-for-agent` tickets for an AFK agent. A Multica leader could instead do the grilling itself.)
2. **Does the squad need many roles?** (`dev-team` v9: 5 agents, test-first by another agent. `dev-flat`: one builder + one independent verifier, skills carry the discipline.)

## Factors

| Factor | Levels |
|---|---|
| **Entry** | **G-in**: the squad's leader grills the requester in Multica (comments/chat). **G-out**: grilling happens outside, in Claude Code with `/grill-with-docs`; the squad receives one `ready-for-agent` issue (agent brief, per `triage/AGENT-BRIEF.md`). |
| **Squad** | `dev-team` (v9), `dev-flat` (builder + verifier), **A**: one bare agent with the same skills and no squad (baseline) |
| **Input quality** | one sentence · three sentences · full spec (the current T2 text, kept as the ceiling control) |

Full cross is too big (cap is 3 runs per cell). Order of play:

1. **Pass 1** — T2 feature, one-sentence input only. Cells: `{dev-team, dev-flat} x {G-in, G-out}` + A (G-in only) = 5 cells x 3 = 15 runs.
2. **Pass 2** — repeat on the best entry for three-sentence and full input.
3. **Pass 3** — a mined real-PR task (`bench/mine_prs.py`), never read while designing.

## Making grilling comparable

Grilling quality varies run to run, which would swamp the squad effect.

- **Simulated requester** (tau-bench style): an LLM holding a hidden *intent* file (what the requester really wants, including 2-3 things they have not thought of). It answers **only what is asked**, one question at a time, in plain non-expert words. Same script, same intent file for every cell.
- **G-in**: the requester answers in the Multica issue comments (script posts replies).
- **G-out**: run `/grill-with-docs` once per task against the same requester, freeze the resulting issue, and give that *identical artifact* to every squad. Record the grilling cost (turns, tokens) separately and add it to the G-out total.
- The frozen G-out artifact removes grilling variance between squads; G-in keeps it because it is part of what G-in is.

## Hidden tests

Test only what any reasonable reader of the **intent** would expect, never private detail. Anything the requester's intent file lists as "not thought of" is tested only if a competent question would have surfaced it. Scope creep is scored: diff touching files/behaviour outside the intent.

## Measures per run (in addition to `rubric.json`)

hidden pass · questions asked by the squad · requester turns · whether each question was one only the requester could answer (vs. answerable from the repo) · `attention_cost` block (visible issues/comments, decisions required, time to first usable result, stall detection latency) · runs, non-cache tokens, wall-clock · scope creep (yes/no + lines).

## What each outcome would mean

- `dev-flat` >= `dev-team` at lower cost and fewer visible issues: v9's roles are a liability; keep the independent verifier only.
- `dev-team` > `dev-flat` on hidden pass or defects caught: independent test-first authorship earns its cost.
- A (bare) ~ `dev-flat`: the squad adds nothing at this task size; the benefit has to be shown on larger tasks.
- G-out >> G-in: the squad should not own clarification; its entry contract is a `ready-for-agent` issue.
- G-in ~ G-out: leader-led grilling is enough and users never leave Multica.

## Rule admission (from mattpocock `SCOPE.md`)

A rule goes into `dev-flat` only if a recorded run failed without it. Candidates carried over from v9 are listed in `bench/failures.md` by id; anything with no failure id stays out until it earns one.

## To build before Pass 1

1. `agents/builder.{json,md}`, `agents/verifier.{json,md}`, `squads/dev-flat.json`.
2. Task variants: `bench/tasks/T2-1sentence.md`, `T2-3sentence.md`, plus `bench/intents/T2.md` (the hidden intent).
3. `bench/requester.py`: simulated requester (reads intent file, answers only what is asked).
4. A frozen G-out artifact for T2 from one `/grill-with-docs` session.
5. `score.py`: record the measures above.
