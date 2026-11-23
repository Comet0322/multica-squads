# 0004 — One builder works test-first; independence moves to the verifier removing the implementation

Status: proposed (config v10, 2026-11-24). **Not verified.** v9 is banked at tag `config-v9`; this must earn its own pass^3 before any claim moves to it.

## Context

ADR 0002 split each ticket into a test stage (`sq-qa`) and an implement stage (`sq-implementer`) so the tests would be written by an agent that never saw the implementation. That split was a hypothesis, not a measured gain: v7 (no test-first) and v8 (split) both passed T3, and v8's one test-related rework (a2, an AC with no test) was caught by the verifier, not by the split. Its costs are real: one more handoff per ticket, so one more context rebuild, and one more internal issue on the board.

We also want to adopt mattpocock's `tdd` skill. It explicitly forbids "horizontal slicing" — all tests first, then all code — which is exactly what v9's single `Red SHA` checkpoint demands.

## Decision

- `sq-qa` is retired (`agents/archive/`). A ticket has two stages: **build** (`sq-implementer`, now tier judgment, with the `tdd` skill, used as written apart from three overrides for working without a person: seams come from the spec, a slice is a criterion, no refactor step) and **docs** (`sq-doc`).
- **The verifier judges the result, not the process.** In a scratch worktree at `Head SHA` it replaces the body of every function the ticket added or changed with a zero-value return (round 2 of the review: restoring files and hand-writing stubs broke on `go.mod`, on large new APIs and on panics), and runs each `AC#`'s tests one at a time, verbosely: each must FAIL with an assertion message. It also requires every test passing at `Base SHA` to still pass, and no test file existing there to change at all. An `I#` (or an `AC#` an earlier ticket delivered) must PASS there and FAIL under a mutation **diff** from the report, which the verifier applies itself. No test line that existed at `Base SHA` may change without a correction or brief authorising it.
- `Red SHA` = `Base SHA`, fixed for the life of the ticket; the range is always `Base SHA..Head SHA`.

### Rejected first draft (b13d6ca)

The first v10 draft required a test-only commit then a code-only commit per criterion, and the verifier walked every commit. The design review (4 auditors, 2026-11-24) found that every check that trusted the builder's account could be bypassed — code first then a claim that the behaviour was "already present", mutation output that existed only as prose, `t.Skip`/build tags/`TestMain` exits passing silently, an unbounded "compile stub", merge commits — and that a per-cycle `Red SHA` broke on a mid-build death and on any history rewrite. All of those were costs of verifying the *process*. Verifying the *result* removes them, because the verifier runs everything itself.

## What is given up

The test writer now knows the implementation it is about to write. The removal check proves each `AC#` test fails without this ticket's implementation and that no pre-existing test was weakened. It does **not** prove the test was written first, nor the test asserts what the spec means rather than what the builder planned. That judgment is the verifier's check 1 (tests against the spec's own text), as it already was in v8 — which is where v8's only test rework was caught.

## How it is decided

Run v10 on T3 and T2-hard, at most 3 runs each, against v9's numbers: pass^3, hidden-test score, runs, non-cache tokens, rework rounds, interventions. If v10 reaches pass^3 at lower cost, the split has no remaining argument. If it fails where v9 passes, record whether the failure is one the separate test writer would have prevented.
