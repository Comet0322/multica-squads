# 2. Tests come first and are written by a different agent; `done` is the only verb

Date: 2026-10-18
Status: accepted, written as config v8. Not yet verified by a run — four probes and a
pass^3 gate stand between this and any claim (see Validation).

Two decisions, recorded together because they are the same move: delete a mechanism whose
guarantee lived in prose, and take the guarantee structurally instead.

## Context

v7 delivered T3 hands-off on its first real attempt (spec `ACHE-152`, hidden 6/6, 0
interventions, 26.6 min). That success is not what this ADR responds to. What it responds
to is how the v7 config got there, and what the run did *not* exercise:

- Four fix rounds and three two-agent audit rounds, all static. Rounds 2 and 3 each
  introduced new stalls that the previous round's fixes had created. Auditing prose against
  prose has no ground truth, so each fix carried its own defect rate and the loop did not
  converge.
- Everything that actually settled a question was *run*: probes F18-F21, the `WillEnqueueRun`
  predicate in `service/issue_trigger.go:126-141`, the B1 run records. The most serious error
  of the day — the belief that reopening an issue to `todo` wakes its assignee — survived
  several audits and was killed by reading the Go source.
- The successful run touched only the happy path. Rework, escalation, a rejected spec check,
  the fast path and PR feedback were never entered once.

Two measured facts shaped the replacement:

1. **A separate QA pass has never caught anything.** Across every scored run on record,
   review rejected 7 times and QA rejected 0: T3/v1/1 2-0, T3/v1/3 2-0, T3/v4/1 3-0,
   T3/v7/1 0-0, T2/v1/1-3 0-0. (The counters are the legacy prose scans and are imprecise,
   and QA ran after review so it saw pre-filtered code. 7-0 is still the only evidence there
   is.)
2. **`blocked` fires no barrier** (`handler/issue_child_done.go:99`, terminal means `done` or
   `cancelled` and nothing else). In a squad with no autopilot — ADR 0001 — `blocked` on its
   own is a permanent stall. v7's remedy was "comment with a roster `mention://` link first,
   *then* `blocked`", an ordering that had to be right, in the one path nothing had run.

## Decision

**1. Tests are written before the code, by an agent that never sees it.**

Every ticket has exactly two stages: `test` (`sq-test-writer`, judgment tier) then
`implement` (`sq-implementer`, execution tier). The test agent reads the acceptance criteria
from the spec and writes tests that fail; the implementer makes them pass and **may never
change or delete a line of a test file that existed at `Red SHA`**. `sq-qa` and `sq-doc` are
retired; documentation is part of the implement stage of the ticket whose behaviour it
describes.

This moves the independent check from after implementation to before it, and converts
verification from judgement into evidence:

| | v7 | v8 |
|---|---|---|
| Judgement happens | after the code, reading a diff | before the code, writing the test |
| Verification asks | "is this implementation right?" | "was it red, is it green, is the scope right?" |
| Independence comes from | a second agent repeating the check | the test author never seeing the implementation |
| Enforced by | an instruction | `git diff --numstat <Red SHA>..HEAD` |

`Red SHA` is the load-bearing artefact: the commit at which the tests were seen to fail,
with the failing output pasted. A test never seen to fail proves nothing about the change
that makes it pass, and "fail for the right reason" is explicit — an assertion about
behaviour, not a compile error.

**2. `done` is the only verb a member has.**

No `@mention`, no `blocked`, no comment on an issue it does not own. An agent that cannot
finish the work still finishes the *issue*: it states what is wrong in its report and sets
itself `done`. The barrier fires, the owner decides. Finishing is the only action that is
certain to produce a wake, so it is the only one used.

The escape hatch is a count, not a status: the owner counts `done → backlog` transitions in
the timeline (`status_changed` entries carry `details.from`/`details.to`), and at two it
stops reworking, sets the ticket's `Result` to `REWORK` and closes it. The leader's table
turns that into `Gate = Decision needed` and the spec goes `in_review`. The human is the
escalation target; no agent escalates to another agent.

A `Cycle` property was designed for this and then deleted: property changes do not appear in
the timeline, so a property cannot count anything — a missed increment leaves no trace.

## Consequences

Good:

- A weakened test is the one failure this design cannot otherwise detect, and it is now a
  `git` command rather than a request in an instruction.
- The branch count in the leader collapses to a four-row table; the ticket has one shape.
  Deleted outright: three ticket shapes, two roles, `blocked`, `mention://`, agent-to-agent
  escalation, the fast path, the `Deliver` ticket, and the `Review verdict`/`QA verdict`
  split.
- PR feedback needs no special path. A fix ticket is an ordinary ticket, it becomes the last
  ticket, and the last ticket's verification *is* the integration check on the head the human
  merges. v7 needed a paragraph to reopen `Deliver` for this.
- Three Opus agents instead of two, but the judgement budget moves from re-reading diffs to
  writing tests rather than growing.

Bad, and accepted:

- Post-hoc independent QA is gone. The 7-0 record says it never paid; if a run ever ships a
  defect that a second empirical pass would have caught, this is the decision to revisit.
- A stall is still unrecoverable without a human, exactly as ADR 0001 chose. The surface is
  smaller — the only wakes are a promotion and a barrier, both measured reliable — but a
  leader that dies mid-wake needs one human message on the spec.
- One `Result` property with one writer loses the role-mismatch guarantee that splitting the
  verdicts bought. There is only one writer, so there is no cross-role write to reject.
- `bench/score.py` reads `Review verdict`/`QA verdict` by name and will not see `Result`.
  Scoring v8 requires that change first.

## Validation

No claim until these pass, in order:

1. A promotion out of `backlog` starts a run on the handoff's assignee.
2. A `child_done` barrier wakes the ticket's owner (`sq-verifier`), not the leader.
3. A stage reopened with two writes runs again, and the owner promotes the right next stage.
4. Two reworks put `Result = REWORK` on the ticket and the spec `in_review` with
   `Gate = Decision needed`.

Then T3 three times hands-off: pass^3. The config is frozen unless a probe fails — the
missing piece in v7 was a terminating condition, not more auditing.
