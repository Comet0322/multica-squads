# Scenario inventory — what kinds of work the squad is asked to do, and what evidence exists

One row per **scenario** (a kind of work; `GLOSSARY.md`). Tiers: **A** scored (pass^n), **B** mechanism
(verified once), **C** refused (must recognise and say so), **D** measured only.
Numbering follows `docs/handoff-v5-open-problems.md` (the original 20). Evidence is what
`results.csv` and `probes.csv` actually record, as of 2026-11-23. **Nothing below has been run on
config v9, on Multica v0.11.0, or on GitHub**: every "pass" is on v6–v8 / Forgejo / Multica 0.8.x.

## The original 20

| # | Scenario | Tier | Task / probe | Evidence | Gap |
|---|---|---|---|---|---|
| 1 | Greenfield project | B | B1 (`csvstat`) | pass on v6, 0 interventions, 34 min | not re-run since v6 |
| 2 | Add a feature to an existing repo | A | `T2-hard` (T2 retired: too easy) | T2 3/3 on v1. **T2-hard validated, never run through a squad** (no rows in `results.csv`) | the one scored task that exists but has no result |
| 3 | Bug from symptoms | A | `T3` | v8 pass^3, hidden 6/6 each | ceiling: v1 also passed 3/3, so success cannot rank versions |
| 4 | Unreproducible bug | C | C1b | refusal pass | — |
| 5 | Wide mechanical refactor | C | C2 | refusal pass | — |
| 6 | Vague requirement | C (inverse) | C3 | pass: asked 5 focused questions, created nothing | only a chat probe; no run that continues after the answers |
| 7 | Multi-repo | C | C4 | refusal pass | — |
| 8 | Tiny change (typo, doc) | — | B3 | deduced, never run; v8 has **no fast path** by decision, so every change pays the 3-stage flow | cost of that decision is unmeasured |
| 9 | Urgent hotfix | C | C5 | refusal pass | — |
| 10 | Requirement changes mid-run | B | B1 scenario-10 check | pass on v6 (spec frozen, change routed as a comment) | not re-run on v8/v9, whose spec/`Spec correction` rules differ |
| 11 | UI / visual work | C | C6 | refusal pass | — |
| 12 | Performance target | C | C7 | refusal pass | — |
| 13 | Irreversible operation | C | C8 | refusal pass | — |
| 14 | Human PR feedback | B | B2 | **trace only**; v8/v9 route it as a comment on the spec | never run |
| 15 | `main` moves during the run | — | none | operating condition, not probed | no rebase/realign step |
| 16 | Several specs concurrently | — | none | documented non-goal | — |
| 17 | Stuck / lost wake | B | F17 fault-injection | passed, but against `sq-medic`, **retired in v7** | probes are stale for v7+; recovery is now `watch.py` + a human |
| 18 | Repo with code but no tests | C | C9 | refusal pass | — |
| 19 | Security / permissions | B | M1–M4 | pass, **all on Forgejo branch protection** | invalid on GitHub until rebuilt; the PR identity is now the user's own account |
| 20 | Long tasks / context size | D | measured in B1, v7, v8 | peak single-run context 65–76k | never tested near a limit |

**Numbering drift to fix:** `probes/B-mechanism-probes.md` calls the PR-comment relay "scenario 8";
the table above (and the handoff doc) call it 14 and call a tiny change 8.

## Candidates raised from how people actually use Multica (not yet numbered)

| Candidate | Why it matters | Possible task / probe | Tier it would sit in |
|---|---|---|---|
| **Add tests to existing code** | Common request, and "does the test actually fail?" is exactly what v9 claims to check | a repo with untested behaviour, hidden mutants the tests must kill | A |
| **Docs-only change** | Light stage exists, but the whole flow is still paid | README + usage examples, hidden check that examples run | A or D (cost) |
| **Ambiguous issue that does have an answer** | Real users write 3 rough sentences | extend C3: answer the leader's questions, then score the result against hidden tests | A |
| **Agent cannot finish → honest stop** | The C-layer only tests refusal at chat time, not giving up mid-run | requirement that becomes impossible after the spec (a hidden contradiction); pass = stops and says so, no fabricated PASS | B |
| **Human comments on a handoff, not the spec** | Platform wakes the member directly (probe v8-P2) and bypasses the owner | one probe per member role | B |
| **A real, unseen bug (holdout)** | Every v8 rule grew from T3's failures; T3 cannot show over-fitting | a small open-source issue pinned at its pre-fix commit, its fix PR's tests as hidden tests; **never read while designing** | A, holdout |
| **Code review as a deliverable** | Plausible first-round use of an agent | a PR with seeded defects; score recall of the seeded ones and false-positive count | new |
| Autopilot (cron) work, chat Q&A, Slack/Telegram triggers, cost/audit | Platform features, not squad design | out of scope for this bench | — |

## Comparison arms (needed before any tier-A result means "squad is better")

No row above says whether the squad beats one agent working alone, which is what Vals.ai's multi-agent
study and Agyn's baselines both vary. Per task, same model and runtime, 3 runs each, with cost and
wall-clock recorded:

1. single agent, default effort
2. single agent, high effort
3. `dev-team` (v9)
4. `bp-team` (the 4-role it235 squad, already synced)

## Order I would run them in

1. v9 on `T3` ×3 in the new environment — re-baselines v9 and exercises the container runtime and the GitHub flow.
2. `T2-hard` ×3 on v9 — the scored task with no result yet.
3. The same two tasks with arms 1–2 — the first time success can be ranked.
4. One holdout task, run once per arm after the design is frozen.
5. Re-run the B probes whose evidence predates v7 (#1, #10, #14, #17, #19).
