# 1. Peer handoff, reopen instead of rework, and no autopilot

Date: 2026-10-17
Status: proposed (v7). Blocked on one platform check, see "Before building this".

## Context

v6 routes every handoff through the leader and recovers stalls with an autopilot
(`sq-medic`). Measured on B1 (spec ACHE-114, 30 issues, 74 runs) and on the F17 probes,
that produced six handoff defects, five of which are a missing step in the protocol rather
than an agent mistake:

1. One leader run created the same rework twice (ACHE-125 12:39:24, ACHE-127 12:39:49,
   both inside the run 12:38:44->12:40:04). The duplicate was acted on and left a stray
   commit that cost an extra cycle to revert. **Handing off means creating an issue, and
   nothing makes that write idempotent.**
2. The handoff carried the task but not the project's conventions, so the only genuine
   rework cycle existed to fix a committed binary and a missing error prefix.
3. PR feedback was to become a handoff under a ticket already `done`, whose stage barrier
   has already fired — a handoff that may never be picked up, silently.
4. The spec sat in `in_review` while the squad was still working, so the handoff to the
   human said "yours" when it was not.
5. The fast path's only structure (handoffs directly under the spec) had no receiving
   branch in the leader's phases.
6. `sq-medic` woke the leader twice when relaying a PR comment, so two leaders could open
   one rework twice.

Underneath them is the structural cost: a reviewer returning work to an implementer goes
reviewer -> leader -> implementer, two hops, with the leader re-deriving state from the
issue tree on each one. B1's leader ran 34 times for 7 tickets.

Three platform facts decide what can replace this:
- An issue assigned to an agent wakes **that agent** when it becomes `todo`. Only *squad*
  assignment is leader-only.
- A `child_done` barrier wakes **the parent issue's assignee**. v6 assigns every ticket to
  the squad, which is why the leader wakes on every stage.
- Status changes are the wake mechanism, and setting a status is idempotent in a way that
  creating an issue is not.

## Decision

**1. The assignee is whoever must act next, and handing off is a status change.**
A member finishing its stage sets its own handoff `done` and sets the next handoff `todo`,
@mentioning its agent. No leader hop. The ban on peer mentions is lifted for this one
purpose: promoting the next stage of the same ticket.

**2. Rework reopens the existing handoff; it never creates an issue.**
CHANGES REQUESTED or FAIL means the reviewer/QA sets the *implement* handoff back to `todo`
with its verdict in a comment, and later sets its own handoff back to `todo` for the
re-check. Setting a status twice is the same as setting it once, so defect 1 cannot recur,
and defect 3 disappears because no handoff is ever created under a finished parent.

**3. Each ticket is owned by its reviewer, not by the squad.**
The ticket issue is assigned to `sq-reviewer`. It therefore receives the ticket's
`child_done` barriers, creates the ticket's three handoffs once on its first wake (and
never again if children already exist), grades, sequences, and sets the ticket `done` —
but only with QA's PASS on record. The implementer never grades its own slice, and the
leader is not involved in a slice at all.

**4. The leader owns the spec and nothing below it.**
Boundary check, the chat, the frozen spec, the ticket plan, promoting the next ticket, the
per-ticket integration check, the spec Status comment and the PR gate. It is woken once per
ticket (that ticket's `done` fires the spec's barrier), not once per stage. Expected leader
runs for a B1-sized spec: ~10 instead of 34.

**5. No autopilots, and therefore no medic and no watcher.**
- *Stall recovery* moves into the agents that are already awake. Every leader and ticket-owner
  wake begins with: the lowest unfinished stage must be `todo`/`in_progress` with a run, or
  newly promoted; a child in `in_review` with its report posted is finished, set it `done`;
  a stage `todo` with no run is `rerun`. Because both are woken by every child completion,
  this covers every stall except one where nothing completes at all.
- *A stall with zero completions is a failure, and the benchmark records it as one.* A timer
  that papers over it inflates exactly the number this project exists to measure, which is
  why `auto_recoveries` was counted separately in the first place.
- *PR feedback arrives as a comment on the spec issue, written by the human*, which wakes the
  leader directly. The spec's "Human gates" line and the PR body both say so. The Forgejo
  VCS webhook never modelled PR comments; polling them was the only reason medic existed as
  a second job, and it brought its own defect class with it.

**6. Escalation is a status change too.** After two failed cycles on the same problem the
ticket owner sets the ticket `blocked`, which fires the spec's barrier and wakes the leader.
This also caps a ticket's barrier count: 3 stages x at most 3 passes = 9, below the
platform's 12-trigger pause (B1's worst issue reached 7).

Roster: `sq-lead`, `sq-implementer`, `sq-reviewer`, `sq-qa`, `sq-doc`. Five agents, no
utilities.

## Consequences

Good:
- Defects 1, 3, 5 and 6 are removed by the structure, not by a rule asking an agent to be
  careful. Defect 5 disappears because members sequence their own stages, so the fast path
  needs no special branch anywhere.
- The review loop is one hop. Fewer hops is less lost information, and it is the only lever
  for that which does not reduce the number of checks.
- Fewer issues per run: B1's 30 become ~26, and F1's three extra rework issues become zero.
- No cron agent, so no run happens that no event asked for.

Bad, and accepted:
- **The conflict of interest moves rather than disappearing.** A reviewer that both grades
  and closes its ticket can rubber-stamp its way to `done`. Three things hold it: QA is a
  different agent and its PASS must be on record, the leader re-checks the branch on its
  one wake per ticket, and the scorer verifies the code independently of every verdict.
- **A stall with no completions is not recovered.** It is measured instead. v4's missed wake
  came from an agent-created wakeup rule being rate-paused, which no version creates any
  more; v5 and v6 families fired every barrier they should have.
- **A human who comments on the pull request instead of the spec issue gets no response.**
  Stated in the PR body and the spec, but it is a worse affordance than relaying.
- Members gain the power to change another issue's status, so a buggy member can disturb a
  stage it does not own. Previously only the leader could.

## Before building this

One platform assumption is load-bearing and unverified: **that a `child_done` barrier wakes
a parent assigned to a member, not only one assigned to a squad.** Everything above rests on
it. It is checkable by hand in about two minutes — create a parent assigned to `sq-reviewer`
with one child, set the child `done`, and see whether a reviewer run appears — and it needs
no squad run. If it turns out barriers only wake squad-assigned issues, decision 3 collapses
and the fallback is: keep the ticket squad-assigned, keep peer promotion (decision 1) and
reopen-instead-of-rework (decision 2), and accept that the leader still receives a cheap
no-op wake per stage.

## Alternatives considered

- *Keep `sq-medic`, fix its two defects.* Rejected: it is a second agent and a cron run that
  no event asked for, it reported stalls that the measurement wants to see, and its relay job
  only existed to spare the human one paste.
- *Leader keeps every ticket, with a no-op wake per stage.* Simpler and keeps one supervisor,
  but leaves the two-hop review loop and 34 leader runs. This is also the fallback above.
- *Let members @mention each other freely.* Rejected: peer mentions outside "promote the next
  stage of this ticket" remove supervision without removing a hop, and nothing then owns the
  ticket.
