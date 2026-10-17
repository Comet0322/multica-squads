# Fault-injection probes — does the squad recover without a person? (scenario 17)

Deterministic probes. Each one builds a scratch issue family that *looks* like a run
whose wake was lost, then leaves `sq-medic` (autopilot `squad-medic`, every 5 min) to
notice. They cost one Haiku scan plus one restarted run each, and do not count against
the scored-run budget.

The scratch families carry the label `run-20261017-medic-probe` and the normal
`spec`/`internal` role labels, so they are indistinguishable from a real run to medic.
They are built with `multica issue update --no-start`, which is what keeps them
run-free: a family with any run in flight is one medic must leave alone.

## Built state (2026-10-17, config 7e943c9)
| Probe | Family | Injected fault | Which medic condition should fire |
|---|---|---|---|
| F17-1 | ACHE-105 (spec, `in_progress`) → ACHE-106 (`done`, report posted) | the stage finished and the parent was never woken — the v4 ACHE-75 failure, reproduced | "the lowest unfinished stage's children are all `done`/`cancelled` (a wake was missed)" |
| F17-2 | ACHE-107 (spec, `in_progress`) → ACHE-108 (`in_review`, report posted) | a handoff delivered its report and nobody promoted it, so no barrier fired | "a child sits in `in_review` with its report already posted" |
| F17-3 | ACHE-109 (spec, `in_progress`) → ACHE-110 (`todo`, assignee sq-doc, zero runs) | the wake that should have started the handoff never arrived | "a child is `todo`/`in_progress` with no run at all" |

Every spec description says **MEDIC PROBE — this is not real work** and tells whoever
is woken to post one comment and stop, so a successful recovery costs one small run
rather than a leader trying to deliver a fictional spec.

## Pass conditions (all of them, per probe)
1. **Detected.** Exactly ONE comment starting `**Medic**` appears on the spec issue,
   naming which issue it detected, how stale the family is, and the wakeup state.
2. **Attributed to an agent.** That comment's timeline entry has
   `actor_type == "agent"`, not `member`. This is what makes recovery free: the v6
   scorer counts only `member` activity and `direct_human` runs as interventions, so a
   recovery must never look like a person. (This is also the one unverified assumption
   in the v6 scorer, settled by this probe.)
3. **Restarted the right issue.** F17-3 restarts the `todo` child (ACHE-110); F17-1 and
   F17-2 have no `todo`/`in_progress` child, so they restart the spec issue itself.
4. **The restart took.** A run actually starts on the restarted issue — `rerun`
   re-enqueues the current assignment and does not depend on a wakeup rule.
5. **Changed no status.** Medic sets no status anywhere (the only exception in its
   instructions is the three-strike escalation, which no probe reaches).
6. **Did not fire early.** No `**Medic**` comment before the family is 10 minutes
   stale. The families were activated at 11:54Z, so the 11:55Z and 12:00Z scans must
   be silent and the 12:05Z scan may act.
7. **One restart per scan.** Three stalled families exist at once; a single medic scan
   must restart exactly one of them.

## Not probed, and why
- The **`wakeup_paused` branch** ("treat it as stalled regardless of the 10 minutes if
  a timeline entry says `wakeup_paused`") cannot be injected: only the platform writes
  that entry, and it takes 12 wakeup fires within an hour to earn it. The generic
  >10-minute branch covers the same state, because a paused rule also means nothing is
  running. Left as a known gap rather than faked.
- **v6 does not use agent-created wakeup rules at all.** ACHE-97 and ACHE-101 (v5) have
  zero rules and their stage barriers fired anyway, so "the leader's wakeup rule was
  disabled mid-run" is not a v6 failure mode; the equivalent fault is the barrier not
  firing, which is F17-1.
