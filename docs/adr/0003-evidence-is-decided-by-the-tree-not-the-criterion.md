# 3. Which evidence a test owes is decided by the tree, not by the kind of criterion

Date: 2026-10-18
Status: accepted, written as config v9. Not yet verified by a run; v9 needs its own pass^3.

Closes the open question `bench/failures.md` F1 left: **what a `Covers:` criterion that
already holds means**, and what the test writer owes for it.

## Context

v8's one rework in three scored runs came from two files that each obeyed themselves.
`qa.md` told the test writer to commit no test for a criterion that already held;
`reviewer.md` required a test for every criterion on the `Covers:` line. T3/v8-a2 took a
rework round for it, and two different v8 reviewer runs invented two incompatible answers
(prove it with a mutation; carve out a `Guards` section).

v9's first attempt was to split the vocabulary: `Acceptance criteria` for behaviour that
does not hold, `Invariants` for behaviour that does, and a different evidence rule for
each. That is the right vocabulary for the **spec**, and it is kept. But as an evidence
rule it does not close: the kind a criterion is and the state of the tree a test runs
against are different facts, and they come apart routinely.

- A stage-1 reopen happens **after** the implement stage has pushed. Resetting that
  stage's issue does not revert its commits, so every `AC#` on the line now passes. This
  is the single commonest rework shape in the design.
- An earlier ticket of the same spec can incidentally satisfy a later ticket's `AC#`.
- Only an `AC#` added by a later `**Spec correction**` can be an `AC#` that holds on
  `main`, because the spec check rejects a spec whose criteria already hold.

Keyed on the criterion's letter, all three demand a red run for behaviour that is present.
No such run exists, so the test writer is caught between its own rules and the verifier's
— which is F1 again, in the vocabulary built to fix it.

## Decision

**One mechanical question decides the evidence, and it is about the tree: is the behaviour
already present where the test runs?**

- **Absent → red evidence.** The test fails on an assertion about behaviour (not a compile
  error, not a missing fixture) at `Red SHA`.
- **Present → mutation evidence.** The test passes, and the proof that it can fail is a
  throwaway change that breaks the behaviour, with the pasted failure, the change
  discarded and never committed.

Three states put the behaviour in the tree, and all three are normal: an invariant; a
reopened test stage after the implement stage pushed; an `AC#` an earlier ticket delivered.
The verifier demands the form the tree implies and is explicitly forbidden to demand red
for behaviour that is present.

The **spec-defect** route survives but is narrowed to what it was always for: an `AC#` that
holds **on `main`**, the spec's own base. That is a numbering mistake in the spec and goes
to the human. An `AC#` that holds only because this spec's own earlier work delivered it is
not a defect in anything.

The criteria split stays, because it answers a different question — *who owes work* — and
answers it well: an `I#` has nothing to implement, and an `I#` that an existing check
already covers needs no ticket at all.

## Consequences

- One rule replaces a branch, in four files that previously had to agree: `qa.md`,
  `reviewer.md`, `definition-of-done` and the glossary. "A test that cannot fail is a bug
  in your work" is now the whole rule, with two forms of proof.
- `Red SHA` stops meaning "the commit where the tests fail". It means "the commit the test
  stage ended on" — the tree the evidence was taken against and the diff base that proves
  no test line was weakened. For an invariant or a present `AC#`, the tests **pass** there.
- Mutation evidence becomes load-bearing vocabulary, co-equal with red evidence rather
  than a weaker substitute, and is in the glossary as such.
- The cost of being wrong is asymmetric and that is deliberate: demanding mutation
  evidence where red was available only wastes a check, while demanding red where it
  cannot exist produces either a test that cannot fail or no test at all — the one failure
  this design has no other way to detect.
- Untested. Mutation evidence has never been produced in a scored run, and the rule's
  hardest path (a stage-1 reopen whose tests now pass) has been reasoned through, not run.
