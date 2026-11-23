# Glossary

The project's vocabulary. Definitions only — no mechanisms, no implementation
decisions (those belong in agent instructions, `bench/`, or an ADR).

## Issue levels

- **Spec issue** — the contract the user approved for one piece of work. The
  only issue level a human is expected to read. Frozen once agreed.
- **Ticket issue** — one independently verifiable behaviour from a spec (a
  vertical slice, not a layer). Child of a spec issue.
- **Handoff issue** — one task for one agent. Internal; humans are not
  expected to read these. One stands alone — the **spec-check handoff**, the
  spec's own first child, which checks the spec before any ticket exists. The
  other two sit under a ticket, which has exactly one of each, in this
  order (config v10; v8 and v9 had a separate test handoff before the
  implement handoff):
  - **Build handoff** — builds the ticket test-first (the `tdd` skill), in
    any commit order. Its tests are proven by the verifier: with every
    non-test file restored to the ticket's base, each `AC#`'s tests must fail.
    May never change a test line that existed at the base.
  - **Docs handoff** — documents what a user can now see. Documentation files
    only. Last, because it commits to the same branch: the head a human merges
    must be a head that was verified.

## Criteria

A spec states what must be true. The two kinds are kept apart because they are
different claims, not because one is weaker.

- **Acceptance criterion** — one numbered, testable statement about behaviour
  that does **not** yet hold **on `main`**. A claim about change.
- **Invariant** — one numbered, testable statement about behaviour that
  **already** holds and must not break. A claim about preservation. Each
  carries `Covered by:` — the existing check that proves it, or `nothing yet`.
- **Retired criterion** — a criterion a human withdrew in a `**Spec
  correction**`, which is the durable record and the only thing that
  authorises deleting a test. A ticket's `Retires:` line marks which ticket
  acts on it; the correction is what makes it retired.

Which **kind** a criterion is decides who owes work for it. It does **not**
decide which form of evidence its test owes — see **Evidence**. An acceptance
criterion an earlier ticket of the same spec happened to deliver is still an
acceptance criterion; it has simply stopped being absent.

## Scenarios and scope

- **Scenario** — a *kind* of work a squad may be asked to do (add a feature to
  an existing repo, fix a bug from symptoms, refactor, …). Not a task: a
  scenario is a category, a task is one concrete instance of it.
- **Task** — one fixed, reusable piece of work used as evaluation input
  (e.g. T3). An instance of a scenario.
- **Scope tier** — how much a given version of the squad commits to a
  scenario:
  - **A (scored)** — must work, measured with scored runs.
  - **B (mechanism)** — must have a working mechanism, verified once.
  - **C (refused)** — not supported; the squad must *recognise* it and say so
    instead of attempting it.
  - **D (measured only)** — observed and recorded, not solved.

## Evidence

- **Scored run** — one complete, hands-off execution of a task, recorded in
  `bench/results.csv` and judged against the success definition. Expensive and
  budgeted.
- **Deterministic probe** — a cheap, repeatable check of one mechanism, whose
  outcome does not depend on chance (fault injection, a chat-only prompt). Not
  a scored run and not counted against the run budget.
- **Red evidence** — the commit at which a test fails, together with the
  failing output. Available only while the behaviour is **absent** from the
  tree the test runs against.
- **Mutation evidence** — for behaviour already **present**: a throwaway
  change that breaks it, the pasted output of the test failing under that
  change, and the change discarded, never committed. Co-equal with red
  evidence, not a weaker substitute.
- Which form a test owes is decided by one mechanical question — is the
  behaviour present in the tree the test runs against? — and never by which
  kind of criterion it came from. What makes a verdict a finding rather than
  an opinion is that the test **was seen to fail**, in whichever form was
  available; a test that was never seen to fail proves nothing about the
  change that makes it pass. Demanding red for behaviour that is present is
  how a squad ends up inventing a failing test, which is worse than no test
  at all.
- **Failure-mode ledger** — the classification of every observed failure by
  cause. A version claims an improvement by showing its targeted failure mode
  no longer occurs, not by a higher pass count.

## Coordination

- **Handoff** — see **Issue levels**. The unit of work one agent is woken for.
- **Owner** — the agent assigned the issue one level above a piece of work: the
  leader owns the spec, the verifier owns every ticket. Coordination is push,
  never pull: a barrier wakes the owner, and only the owner promotes.
- **Brief** — a `**Brief (cycle N)**` comment an owner posts on an issue it is
  sending back, naming exactly what to fix. Its `N` is `1 + the briefs already
  on that issue` and never resets, so the reader can order them.
- **Report** — a `**Report (cycle N)**` comment an agent posts on its **own**
  issue, carrying pasted command output. The only way work becomes visible one
  level up.
- **Relay** — a `**Relay**` comment on the spec issue quoting a person who
  commented somewhere no one may answer them. The sole exception to "comment
  only on your own issue", because it is the only path from a member to the
  leader.
- **Rework round** — one send-back of one ticket, counted by its briefs. The
  budget is per ticket and resets when a human changes the inputs; the brief's
  own label does not.
- **Reconcile wake** — an owner wake that carries nothing new, because the
  barrier rule re-fires on any child status change. Recognised by state, never
  by timestamps — and never by a `Result` alone: a select property cannot be
  unset, so a stage keeps the last verdict written on it straight through a
  reopen. The state is a verdict **plus** the evidence it was reached at, which
  is why the owner's own report records the SHAs it judged.
- **Ticket base** — the commit a ticket's work starts from: `main` for the
  first, the previous ticket's verified head otherwise. Written on the ticket,
  because order cannot be inferred.
- **Integration check** — the last ticket's own build-stage (stage 1) verification, widened
  to every criterion some ticket owed evidence for. An invariant an existing
  check already covers is discharged by running that check on the head, not
  by looking for a ticket that covered it. There is no separate integration
  stage: the head a human merges is a head that was verified as part of a
  ticket.

## Reliability

- **Reliable** — passing repeatedly, not passing once. Always stated with the
  number of runs behind it; with three runs the honest claim is "no
  instability seen", never a probability.
- **Human intervention** — any action by a *person* on a run's issues
  (status change, comment, wake). Must be zero for a run to succeed. A
  requirements chat before the run is not an intervention.
- **Automated recovery** — an action by a non-human actor that unblocks a
  stalled run. Counted separately from human intervention because it means the
  squad recovered, not that the human did. A squad may provide no such actor, in
  which case the count is structurally zero and a stall is simply a failure.
- **Human gate** — a point where the design *intends* to wait for a person.
  Declared in the spec. A gate is not an intervention.
