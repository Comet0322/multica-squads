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

---

# Results, 2026-10-17 (config 667c66b)

**F17-3 — pass.** The 12:05Z scan found ACHE-110 `todo` with no run, posted one
`**Medic**` comment naming the detection (11 minutes stale, no in-flight run, no
`wakeup_paused`, 0 prior Medic comments), restarted the child — the correct target
under step 5b — and changed no status. sq-doc then ran, set its handoff `done`, the
stage barrier woke the leader, and the leader re-derived the state correctly. Scored
with the fixed scorer: `human_interventions = 2` (the two status changes used to build
the family, which really were a person's) and `auto_recoveries = 1`.

**F17-2 — pass, with a defect found.** Detected at 12:10Z, 16 minutes stale, correct
comment, no status changed. But it cost **two leader runs 30 seconds apart**: medic's
comment on a squad-assigned issue wakes the leader by itself, and the `issue rerun`
that followed woke it again. Two leaders seeing the same state can promote a stage or
open a rework twice, so this is a correctness risk, not only a wasted Opus run. Fixed
in `agents/medic.md` (667c66b): a child is rerun directly, but for a spec-level
restart medic checks `issue runs --active` after commenting and reruns only if nothing
is running. Re-probed as F17-2b.

**F17-1 — void: the injected fault did not exist.** `issue update --no-start`
suppresses the run on the issue being updated but **not the parent's stage barrier**.
Setting ACHE-106 `done` fired `child_done` on ACHE-105 22 seconds later; the leader
ran and handled it, so the family never became stale enough for medic. This is a
better outcome than the probe: the v4 failure (leader never woken after a stage
finished) came from an **agent-created** wakeup rule that the platform rate-paused,
and v6 does not use those — its platform stage barriers fired correctly here.

**Timing and the one-restart rule — pass.** Three families were activated at 11:54Z.
The 11:55Z and 12:00Z scans were silent (inside the 10-minute bound) and the 12:05Z
scan acted on exactly one family.

**Two measurement facts settled** (both now in `failures.md`): an agent running the
`multica` CLI is recorded as `actor_type: agent`, so a recovery is never mistaken for
a person; and a run started by `multica issue wakeup trigger` carries
`attribution.source = trigger_owner`, which the old scorer did not look at.

**Not tested, and why.** The leader's own self-heal of a handoff stuck in `in_review`
(set it `done` and continue) was NOT exercised by F17-2: the probe contract told the
leader to cancel the spec and stop instead. F17-2b covers it.
