# 1. Ownership per level, rework by reopening, and no autopilot

Date: 2026-10-17
Status: accepted, implemented as config v7. Both load-bearing platform assumptions were
verified first (probe F18, below).

## Context

v6 routed every handoff through the leader and recovered stalls with an autopilot
(`sq-medic`). Measured on B1 (spec ACHE-114, 30 issues, 74 runs) and the F17 probes, that
produced six handoff defects, five of them a missing step in the protocol rather than an
agent mistake:

1. One leader run created the same rework twice (ACHE-125 12:39:24, ACHE-127 12:39:49, both
   inside the run 12:38:44->12:40:04). The duplicate was acted on and left a stray commit
   that cost an extra cycle to revert. **Handing off meant creating an issue, and nothing
   made that write idempotent.**
2. The handoff carried the task but not the project's conventions, so the only genuine
   rework cycle existed to fix a committed binary and a missing error prefix.
3. PR feedback was to become a handoff under a ticket already `done`, whose stage barrier
   had already fired — a handoff that may never be picked up, silently.
4. The spec sat in `in_review` while the squad was still working, so the handoff to the
   human said "yours" when it was not.
5. The fast path's only structure had no receiving branch in the leader's phases.
6. `sq-medic` woke the leader twice when relaying a PR comment, so two leaders could open
   one rework twice.

Underneath them was the structural cost: a reviewer returning work to an implementer went
reviewer -> leader -> implementer, two hops, with the leader re-deriving state each time.
B1's leader ran 34 times for 7 tickets.

## What the platform actually allows (probe F18, 2026-10-17)

Two assumptions decided whether a different shape was possible. Both were measured on a
hand-built family (parent ACHE-144 assigned to `sq-reviewer`, child ACHE-145), not assumed:

- **A `child_done` barrier wakes the parent issue's assignee even when that is an individual
  agent.** Setting the child `done` at 14:04:39 started a run on the parent in the same
  second: agent `sq-reviewer`, `wakeup_system_rule: child_done`, `is_leader_task: None`.
  Only *squad* assignment is leader-only. v6 assigned every ticket to the squad, which is
  the entire reason the leader woke on every stage.
- **Reopening a completed stage and completing it again re-fires the barrier.** The child was
  set back to `todo` and then `done` again at 14:06:21; a second `child_done` run appeared
  within 15 s. So a status change can carry a handoff, and `--no-start` on the child does not
  suppress the parent's wake (already known from F17-1).

- **The barrier wakes the owner but does not promote the next stage.** Probe F19: completing
  stage 1 fired one `child_done` run on the parent while the stage-2 child sat in `backlog`
  for 75 s. Sequencing is the owner's act, not the platform's.

The CLI documents the third piece: `--stage` groups children into "an ordered barrier group
under its parent; **the parent assignee is woken only when every sub-issue in a stage
finishes**", and `issue children` reports `total`/`done` per stage.

Measured after this decision was taken, and it closes off one alternative: Claude Code's
Agent Teams coordinate by **pull** — finishing a task unblocks its dependents and any free
teammate claims one, so no wake is spent on sequencing. Multica offers no unblock-and-claim,
so coordination here is necessarily **push**: the barrier wakes an owner and the owner
promotes. The one judgment wake per stage is a platform cost, not a design choice.

## Decision

**1. Ownership is per level, and a stage barrier delivers the handoff.**
The spec belongs to `sq-lead`, each ticket to `sq-reviewer`, each handoff to its assignee.
Finishing your own issue IS the handoff: the barrier wakes the owner of the level above
within seconds. Nothing is nudged, nothing is created to pass work on, and no member ever
mentions a peer or changes another issue's status — so the ban on peer mentions stays.

**2. Rework reopens the existing handoff; it never creates an issue.**
CHANGES REQUESTED or FAIL means the owner sets the *implement* handoff back to `todo` with a
comment naming what to fix. Setting a status twice is the same as setting it once, so defect
1 cannot recur, and defect 3 disappears because nothing is ever created under a finished
parent. Verified above that the reopened stage wakes the owner again when it completes.

**3. A ticket's children are only the stages that belong to other agents.**
A feature ticket has two: stage 1 implement (`sq-implementer`), stage 2 qa (`sq-qa`). There
is **no review handoff** — the review happens in the wake the barrier gives the owner, on
the ticket itself. A separate review issue assigned to the owner would have been woken twice
for one event (once by its own promotion, once by the barrier), which is defect 6 growing
back in a new place. The Deliver ticket has three: integration-qa, docs, open PR.

**4. The leader owns the spec and nothing below it.**
Boundary check, chat, the frozen spec, the ticket plan, promoting the next ticket, a brief
integration check per ticket, the Status comment, the PR gate, and fix tickets for human
feedback. It is woken once per ticket. Expected ~8 leader runs for a B1-sized spec instead
of 34.

**5. No autopilots, so no medic and no watcher.** Both deleted; both agents archived.
- *Stall recovery moves into the agents that are already awake.* Every leader and owner wake
  begins by re-checking its own level: a child in `in_review` with its report posted is set
  `done`; a child `todo`/`in_progress` with no active run is `rerun`; anything moving is left
  alone. Because both are woken by every completion at their level, this covers every stall
  except one where nothing completes at all.
- *A stall with zero completions is a failure, and the benchmark records it as one.* A timer
  that papers over it inflates exactly the number this project exists to measure, which is
  why `auto_recoveries` was counted separately in the first place. An agent-created wakeup
  rule is not an escape either: that is what the platform rate-paused in v4, the only
  intervention v4 ever needed.
- *PR feedback arrives as a human comment on the spec issue*, which wakes the leader
  directly. The spec's "Human gates" line, the Status comment and the PR body all say so.
  The VCS webhook never modelled PR comments; polling them was medic's whole second job and
  it brought defect 6 with it.

**6. Escalation is a status change.** After two failed cycles on one problem the ticket's
owner sets the ticket `blocked`, which fires the spec's barrier and wakes the leader. This
also caps a ticket's barrier count at about 3 stages x 3 passes = 9, below the platform's
12-trigger pause (B1's worst issue reached 7).

Roster: `sq-lead`, `sq-implementer`, `sq-reviewer`, `sq-qa`, `sq-doc`. Five agents, no
utilities, no cron.

## Consequences

Good:
- Defects 1, 3, 5 and 6 are removed by the structure rather than by a rule asking an agent
  to be careful. Defect 5 disappears because the fast path is now just a ticket with two
  stages, so no phase needs a special branch for it.
- The review loop is one hop instead of two, which is the only way to lose less information
  across a handoff without removing a check.
- Fewer issues: a feature ticket has 2 children instead of 3, and reworks add none. B1's 30
  issues would be about 23.
- No run happens that no event asked for.

Bad, and accepted:
- **The conflict of interest moves rather than disappearing.** An owner that both grades and
  closes its ticket could rubber-stamp its way to `done`. Three things hold it: QA is a
  different agent and its PASS must be on record before the ticket may close, the leader
  re-checks the branch on its one wake per ticket, and the scorer verifies the code
  independently of every verdict.
- **A stall with no completion is not recovered, only measured.** v4's missed wake came from
  an agent-created wakeup rule being rate-paused, which no version creates any more, and
  every v5/v6 barrier fired when it should have.
- **A human who comments on the pull request instead of the spec issue gets no response.**
  Stated in three places, but it is a worse affordance than relaying was.
- **Members may now be reopened rather than re-briefed.** An implementer must read the newest
  comment on its own issue to know what changed, instead of receiving a fresh issue.

## Alternatives considered

- *Keep `sq-medic` and fix its two defects.* Rejected: a second agent plus a cron run that no
  event asked for, reporting stalls the measurement wants to see, for a relay job that only
  spared the human one paste.
- *Leader keeps every ticket, with a cheap no-op wake per stage.* Simpler and keeps one
  supervisor, but leaves the two-hop review loop and 34 leader runs. This was the fallback if
  F18 had shown barriers only wake squad-assigned issues.
- *Let members @mention each other freely.* Rejected, and made unnecessary: with ownership per
  level the barrier already delivers the work, so a peer mention would add a second wake for
  one event — the defect it was meant to avoid.
