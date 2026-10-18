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
  other three sit under a ticket, which has exactly one of each, in this
  order:
  - **Test handoff** — turns a ticket's acceptance criteria into executable
    tests that fail. Written without sight of any implementation.
  - **Implement handoff** — makes those tests pass. May add tests; may not
    change or delete the ones the test handoff wrote.
  - **Docs handoff** — documents what a user can now see. Documentation files
    only. Last, because it commits to the same branch: the head a human merges
    must be a head that was verified.

## Criteria

A spec states what must be true. The two kinds are kept apart because they have
different evidence, and confusing them asks for a failing test that cannot exist.

- **Acceptance criterion** — one numbered, testable statement about behaviour
  that does **not** yet hold. Its evidence is red: a test that fails before the
  change exists, for the right reason, and passes after.
- **Invariant** — one numbered, testable statement about behaviour that
  **already** holds and must not break. It can have no red evidence, because
  there is nothing to make fail. Its evidence is that it passes on every
  verified head. An invariant is not a weaker acceptance criterion; it is a
  different claim, about preservation rather than change.

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
- **Red evidence** — the commit at which a ticket's tests fail, together with
  the failing output. What makes a verdict a finding rather than an opinion: a
  test that was never seen to fail proves nothing about the change that makes
  it pass. Only an **acceptance criterion** has red evidence. An **invariant**
  has none by definition, so demanding it is how a squad ends up inventing a
  failing test, which is worse than no test at all.
- **Failure-mode ledger** — the classification of every observed failure by
  cause. A version claims an improvement by showing its targeted failure mode
  no longer occurs, not by a higher pass count.

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
