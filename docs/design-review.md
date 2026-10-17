# Squad design review criteria

How to audit this squad's configuration **without running it**. Every item below is a
question with a yes/no answer, a way to check it from the config and the measured
platform fact it rests on. A review reports each failure as
`file:line` + the concrete failure scenario it produces — never as a style opinion.

This file is the standard; `bench/failures.md` is the record of what it has caught.

## The wake inventory (the review's centre)

Nothing in this squad runs on a timer, so every step forward is one wake. The design is
only alive if each row below is the **only** wake for its event.

| # | Event | Mechanism | Woken |
|---|---|---|---|
| 1 | the user says something in chat | chat | `sq-lead` |
| 2 | the leader promotes a ticket `backlog` → `todo` | status change starts a run | `sq-reviewer` (the ticket's assignee) |
| 3 | an owner promotes a stage `backlog` → `todo` | status change starts a run | that handoff's assignee |
| 4 | a handoff finishes (`done`) | stage barrier (`child_done`) | the **parent's** assignee |
| 5 | a ticket finishes (`done`) | stage barrier on the spec | `sq-lead` (squad assignee → leader only) |
| 6 | an agent cannot continue (`blocked`) | an `@mention` of its owner in a comment on its own issue | that owner |
| 7 | a human comments on the spec issue | comment on a squad-assigned issue | `sq-lead` |
| 8 | the human merges the PR | Forgejo webhook + `Closes <SPEC-ID>` | nothing; the spec goes `done` |
| 9 | a level is stalled and its owner is awake | `multica issue rerun <ticket-id>` | that ticket's owner |

Forbidden, because they produce a **second** wake for one event:
- an `@mention` of your owner in a report (row 4 already wakes it, ~1 s later, and the two
  are not deduplicated — they are on two different issues),
- a comment *and* a status change for the same transition (post the comment first with no
  mention; the status change is the wake),
- a `rerun` on an issue that was just commented on.

## W — wakes

- **W1** Does every event that must move work appear in the inventory above, with exactly
  one mechanism? Check: walk each agent's phase list and name the row for each transition.
- **W2** Does any instruction produce two wakes for one event? Check: grep for `@mention`
  and for a comment followed by a status change on the same issue.
- **W3** Does any instruction expect a wake from a status the platform does not fire on?
  Only `done` and `cancelled` are terminal; `blocked`, `in_review` and `todo` fire **no**
  barrier. Check: grep for `blocked` and `in_review` near the word *barrier* / *wakes*.
- **W4** Is every wake the design relies on either measured in `CLAUDE.md` or read out of
  the platform source? An unverified wake is a stall waiting to happen.
- **W5** Can a parent be left in `backlog` or `done` while its children still run? Both
  suppress the child-done notification entirely, so the completion is lost.
- **W6** Does any stage complete while a **lower** stage is non-terminal? The barrier only
  evaluates on the completing child and requires every stage ≤ its own to be terminal, so
  that completion wakes nobody.

## O — ownership

- **O1** Does every issue have exactly one owner (spec → `sq-lead`, ticket → `sq-reviewer`,
  handoff → its assignee)?
- **O2** Does any instruction tell an agent to change an issue it does not own? Allowed:
  your own issue; an owner on its own direct children. Never a sibling, a peer's issue, or
  a parent's status or description.
- **O3** Is sequencing at each level done by exactly one agent? Two agents promoting the
  same stage means the work is done twice.
- **O4** Does the escalation path stay inside ownership (a comment on your own issue, not a
  write to your parent)?

## R — reachability

- **R1** Is every branch in an owner's phase list reachable — is there a row in the wake
  inventory that produces it?
- **R2** Does every structure the design can create have a handler in the agent that
  receives it? Enumerate the shapes: spec + spec-check, feature ticket, `Deliver` ticket,
  fast-path ticket, fix ticket, reopened ticket. A shape with no handler means an agent
  improvising on the only structure that path can produce.
- **R3** Does every path reach either the human gate or an explicit stop? No state may be
  terminal-by-accident: a ticket nobody will wake, a spec that never reaches `in_review`.
- **R4** Is the last step before the human gate always a whole-spec check on the head the
  human will merge?

## S — state truthfulness

- **S1** Does an agent ever **infer** which event woke it when the platform states it? The
  child-done system comment names the stage that closed, the sub-issue that finished and
  the next stage. Deriving that from `total`/`done` counts is wrong after any reopen.
- **S2** After a reopen, do the stage counts and the properties still describe reality?
  Reopening a lower stage must reset the higher stages that have to run again, or a later
  wake reads a stale `done` and a stale verdict.
- **S3** Is every property read guarded by what makes it current — `Head SHA` for a verdict,
  the cycle number for a brief? Property changes do not appear in the timeline, so a
  property is only ever the *final* value.
- **S4** Can two cycles on one issue be told apart? `**Brief (cycle N)**` /
  `**Report (cycle N)**`, newest in force.
- **S5** Does each closed vocabulary have exactly one meaning, written by exactly one role?

## C — consistency

- **C1** Does each rule live in exactly one place, and is it contradicted nowhere? A skill
  does not outrank the platform workflow, so a status override must live in an agent's own
  `.md`.
- **C2** Does every agent that can receive a **reopened** issue know the cycle rules?
- **C3** Do the terms match `GLOSSARY.md`?
- **C4** Does `CLAUDE.md`'s flow description match what the agents actually do?
- **C5** Are there leftovers from an earlier version — a role, a mention, an issue level or
  a utility that no longer exists?

## E — evidence

- **E1** Is every claim an instruction makes about the platform traceable to a measured fact
  or to the source? Reasoning is not a fact.
- **E2** Does every verdict, baseline and "it works" require **pasted output**?
- **E3** Is the capability boundary established by running, not by reading?

## $ — cost

- **$1** Does any instruction create a run that does no work? (B1: 18 of 74 runs started
  within 3 s of a comment — the report-mention double wake.)
- **$2** Does any issue approach the platform's 12-trigger `child_done` pause?
- **$3** Is anything re-read or re-run that an earlier stage already recorded?

## Platform facts this standard depends on

| Fact | Source |
|---|---|
| the barrier fires only on non-terminal → terminal, where terminal = `done` or `cancelled` | `handler/issue_child_done.go:99` |
| the barrier's system comment names the closed stage, the finished sub-issue and the next stage | `handler/issue_child_done.go:366`, `stageProgressSummary` |
| the barrier closes only when every stage ≤ the completing child's stage is terminal | `stageBarrierClosed`, same file `:571` |
| a parent in `backlog`, `done` or `cancelled`, or assigned to a human, gets no notification at all | same file `:118`–`:131` |
| wake deduplication is per (issue, agent), so a mention on the child and a barrier on the parent are two runs | `HasPendingTaskForIssueAndAgent`, same file `:914` |
| a squad-assigned parent wakes the **leader only**, with no member fan-out | `triggerChildDoneSquad`, same file |
| a status change starts a run unless `--no-start` is passed; creating an issue has no such flag, so handoffs are created `backlog` and promoted | `multica issue status --help`; B1 `ACHE-122` created `backlog` 12:35:47, promoted 12:35:53, run 12:35:53 |
| an `@mention` in a comment wakes the mentioned agent even on an issue it is not assigned | B1 `ACHE-122`: the implementer's report mentioned `sq-lead`, which ran at 12:36:25 while the barrier ran on the parent at 12:36:26 |

## How to run the review

1. Read every file in `agents/`, `skills/`, `squads/`, `properties/` and `CLAUDE.md`.
2. Build the wake inventory from the instructions as written, and diff it against the table
   above — a missing row is a stall, an extra row is a duplicate.
3. Answer every item W1..$3 with yes/no and the evidence.
4. For each failure, give `file:line`, the scenario (what happens, step by step) and the
   smallest fix. Rank by whether it stops a run, weakens a guarantee, or costs tokens.
5. Claim nothing that needs a run to know. Say "needs a run" instead.
