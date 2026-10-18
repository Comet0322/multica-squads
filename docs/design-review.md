# Squad design review criteria

How to audit this squad's configuration **without running it**. Every item below is a
question with a yes/no answer, a way to check it from the config and the measured
platform fact it rests on. A review reports each failure as
`file:line` + the concrete failure scenario it produces — never as a style opinion.

This file is the standard; `bench/failures.md` is the record of what it has caught.

## The wake inventory (the review's centre)

Nothing in this squad runs on a timer, so every step forward is one wake. The design is
only alive if each row below is the **only** wake for its event.

**A run starts on an issue in exactly three ways** (`service/issue_trigger.go:126-141`):
created in a status other than `backlog`; its assignee changes while it is not `backlog`;
its status moves **out of `backlog`** into something not `done`/`cancelled`. Every row below
is one of those, a stage barrier, a `mention://` link, or chat. A transition that is none of
them moves nothing — and says nothing, because the CLI reports the status change anyway.

| # | Event | Mechanism | Woken |
|---|---|---|---|
| 1 | the user says something in chat | chat | `sq-lead` |
| 2 | the leader promotes a ticket out of `backlog` | status change starts a run | `sq-reviewer` (the ticket's assignee) |
| 3 | an owner promotes a stage out of `backlog` | status change starts a run | that handoff's assignee |
| 4 | a handoff finishes (`done`) | stage barrier (`child_done`) | the **parent's** assignee |
| 5 | a ticket finishes (`done`) | stage barrier on the spec | `sq-lead` (squad assignee → leader only) |
| 6 | an agent cannot continue | **nothing — it still sets its own issue `done`** and says why in its report, which fires the barrier normally. v8 removed `blocked` and `@mention` from every agent (ADR 0002): `blocked` is non-terminal so it fires no barrier, and a mention is a second wake nobody needs. A config in which this row names a mention is a config with an unreachable escalation path. | that issue's owner, by the ordinary barrier |
| 7 | a human comments on the spec issue | comment on a squad-assigned issue | `sq-lead` |
| 7b | a human comments on a **ticket or handoff** (agent-assigned) | a *human's* comment does wake an agent-assigned issue's assignee — measured, probe v8-P2 — unlike an agent's, which wakes nobody | that issue's assignee, which is **not** the leader. It must act on nothing and post a `**Relay**` on the spec issue — the one comment an agent may make outside its own issue, and the only path from a member to the only agent allowed to answer a person. Without that rule the human's words die there, and the assignee acts on prose that never entered the spec |
| 8 | the human merges the PR | Forgejo webhook + `Closes <SPEC-ID>` | nothing; the spec goes `done` |
| 9 | an owner restarts a child: rework, a decision the human supplied, a stalled stage, a reopened ticket | `status <id> backlog` (starts nothing), then `status <id> todo` — **two** writes | that child's assignee |
| 10 | an owner promotes the next stage while a lower stage is already complete | the **same** `child_done` rule re-evaluating (it is `mode: continuous` on `issue.status_changed`, condition `children_done / each_stage`) | that owner, a second time, for the stage that already closed |

Row 10 is not a design choice and cannot be removed: the barrier rule has no memory of
having fired, so it re-fires on **any** child status change while some stage is fully
terminal — and row 3, the owner's own promotion, is such a change. One extra owner wake per
stage transition is therefore structural. The only defence is that every owner wake starts
by re-checking its own level and leaves anything already moving alone; measured working in
T3/v7-a1 (stage-1 barrier re-fired at 16:32:24 as F1 was promoted; the second leader run
logged `no_action — "Stage-1 barrier re-fired; F1 already promoted and running"`). An owner
whose first act is to advance a stage, rather than to look at what is already running,
promotes twice.

Forbidden, because they produce a **second** wake for one event:
- a `mention://` link to your owner in a report (row 4 already wakes it, ~1 s later, and the
  two are not deduplicated — they are on two different issues),
- any agent comment on the squad-assigned **spec** issue by someone other than the leader —
  **except a `**Relay**` quoting a person who commented on an issue of that agent's own.**
  That one is deliberate and worth its single wake: it is the only path from a member to
  the leader, and row 7b is otherwise a human talking into a void,
- a `rerun` on an issue whose comment can wake its owner by itself.

Forbidden, because they produce **no** wake while looking like one:
- `done → todo` or `blocked → todo` as a single write (row 9 exists for this),
- a comment as a way of asking an agent to do something, without a `mention://` link,
- `blocked` on its own as a way of escalating.

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
  that completion wakes nobody. One stage, and one ticket, is restarted at a time.
- **W7** Is every start and restart a transition **out of `backlog`**? Grep every
  `status <id> todo` and check what the issue's status is at that moment. This is the item
  that catches the most dangerous class of defect here, because the failure is silent: the
  board shows `todo`, no agent is running, and nothing is watching.

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
  receives it? Enumerate the shapes: spec + spec-check, ticket, reopened ticket, a ticket
  added after the "last" one by PR feedback, a ticket carrying a `Retires:` line, a stage
  reopened after a later stage has already pushed. (v7 removed ticket shapes: there is no
  `Deliver` ticket and no fast path, so a config in which those appear is out of date.) A
  shape with no handler means an agent improvising on the only structure that path can
  produce.
- **R3** Does every path reach either the human gate or an explicit stop? No state may be
  terminal-by-accident: a ticket nobody will wake, a spec that never reaches `in_review`.
- **R3b** Which stalls can the squad recover from, and which can it not? Be exact, because
  the owner's self-recovery is weaker than it reads. An owner only re-checks its level
  **on a wake**, so recovery needs a wake to arrive. After promoting stage 2 or 3 one does:
  the promotion is a child status change while a lower stage is already terminal, so row 10
  re-fires the barrier within seconds and the owner gets a free second look. After
  promoting a ticket's **stage 1**, or the spec-check, **no stage is terminal yet, so no
  barrier can fire and the owner has no further wake at all.** A first stage that completes
  its run while leaving its own issue non-terminal (`in_review`, or reset to `todo` by the
  platform's sweeper, which is a single write and starts nothing) is therefore an
  unrecoverable stall by design, with the human as the only recovery path. That is ADR
  0001's accepted position, not an oversight — but a design that claims blanket
  self-recovery is overclaiming, and the detector (`watch.py`'s `STALLED`) is what makes it
  visible. Measured: 0 occurrences in 211 runs.
- **R3c** The same class, one level up: a run that ends `completed` having made some of its
  level's writes but not the next one. Each of these leaves a state whose recovery **is**
  written — and no wake that reaches it, because the barrier already fired and nothing
  changes a child's status again: a stage set `Result` but not promoted; a ticket given
  `Result` but not set `done`; tickets created but the first never promoted; a PR opened
  but `Gate` never set (which also leaves the spec `in_progress`, so section 1's
  one-spec-at-a-time check blocks the next spec). Enumerate them and keep the list honest:
  an owner's self-recovery is only as good as the wakes that can carry it, and prose that
  reads as if recovery were live is the thing this row exists to catch. Same accepted
  position as R3b — the human recovers, the detector makes it visible.
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

- **$1** Does any instruction create a run that does no work? (B1: 17 of 74 runs were woken
  by a comment — the report-mention double wake. An escalation is also a comment wake, and is
  counted separately because it is the only wake out of `blocked`.)
- **$2** Does any issue accumulate an unbounded number of wakes? (The 12-trigger pause seen
  on v4's `ACHE-75` applied to an **agent-created** wakeup rule, not to the platform barrier,
  so this is a cost question now, not a correctness one.)
- **$3** Is anything re-read or re-run that an earlier stage already recorded?

## Platform facts this standard depends on

| Fact | Source |
|---|---|
| a run starts only on create-not-in-backlog, an assignee change, or a move out of `backlog`; `done → todo` and `blocked → todo` start nothing | `service/issue_trigger.go:126-141`, the one predicate both write paths call |
| an agent's comment on an issue assigned to another **agent** starts nothing without a `mention://` link; on a **squad**-assigned issue any agent comment wakes the leader | `handler/comment.go` assignee fallback (member-only) + the squad-leader fallback |
| a mention must be the link form `[@Name](mention://agent/<id>)`; a plain `@name` parses as nothing | `util/mention.go:16`; the runtime prompt states the form and its effect |
| `--siblings` is rooted at the issue's **parent**: that parent plus every child of it, active only, capped at 20 — it never reaches grandchildren | `queries/agent.sql:2553` + `multica issue runs --help` |
| the barrier fires only on non-terminal → terminal, where terminal = `done` or `cancelled` | `handler/issue_child_done.go:99` |
| the barrier's system comment names the closed stage, the finished sub-issue and the next stage | `handler/issue_child_done.go:366`, `stageProgressSummary` |
| the barrier closes only when every stage ≤ the completing child's stage is terminal | `stageBarrierClosed`, same file `:571` |
| a parent in `backlog`, `done` or `cancelled`, or assigned to a human, gets no notification at all | same file `:118`–`:131` |
| wake deduplication is per (issue, agent), so a mention on the child and a barrier on the parent are two runs | `HasPendingTaskForIssueAndAgent`, same file `:914` |
| a squad-assigned parent wakes the **leader only**, with no member fan-out | `triggerChildDoneSquad`, same file |
| `issue create` has no `--no-start`, so an issue created in any status but `backlog` starts a run at once; `--no-start` exists only on `issue status`/`issue update` | `multica issue create --help`; B1 `ACHE-114` (created `in_progress`) ran at creation, `ACHE-115` (created `backlog`) did not |
| an `@mention` in a comment wakes the mentioned agent even on an issue it is not assigned | B1 `ACHE-122`: the implementer's report mentioned `sq-lead`, which ran at 12:36:25 while the barrier ran on the parent at 12:36:26 |

## How to run the review

1. Read every file in `agents/`, `skills/`, `squads/`, `properties/` and `CLAUDE.md`.
2. Build the wake inventory from the instructions as written, and diff it against the table
   above — a missing row is a stall, an extra row is a duplicate.
3. Answer every item W1..$3 with yes/no and the evidence.
4. For each failure, give `file:line`, the scenario (what happens, step by step) and the
   smallest fix. Rank by whether it stops a run, weakens a guarantee, or costs tokens.
5. Claim nothing that needs a run to know. Say "needs a run" instead.
