# 0004 — One builder works in vertical slices; independence moves to the verifier's commit checks

Status: proposed (config v10, 2026-11-24). **Not verified.** v9 is banked at tag `config-v9`; this must earn its own pass^3 before any claim moves to it.

## Context

ADR 0002 split each ticket into a test stage (`sq-qa`) and an implement stage (`sq-implementer`) so the tests would be written by an agent that never saw the implementation. That split was a hypothesis, not a measured gain: v7 (no test-first) and v8 (split) both passed T3, and v8's one test-related rework (a2, an AC with no test) was caught by the verifier, not by the split. Its costs are real: one more handoff per ticket, so one more context rebuild, and one more internal issue on the board.

We also want to adopt mattpocock's `tdd` skill. It explicitly forbids "horizontal slicing" — all tests first, then all code — which is exactly what v9's single `Red SHA` checkpoint demands.

## Decision

- `sq-qa` is retired (`agents/archive/`). A ticket has two stages: **build** (`sq-implementer`, now tier judgment, with the `tdd` skill) and **docs** (`sq-doc`).
- The builder works per criterion: a **test commit** (test files only, plus a compile stub) followed by a **code commit** (no test files), or a test commit alone where the behaviour is already present.
- `Red SHA` now means the commit the build started from; `Head SHA` the last it pushed.
- The verifier (`reviewer.md` §3) walks every commit in `Red SHA..Head SHA`: a commit that mixes test and non-test files is rejected; every test commit is checked out and must fail on an assertion (behaviour absent) or carry mutation evidence (present, ADR 0003 unchanged); no code commit may touch a test file. The rest of v9's stage-2 checks (suite, scope, intake baseline, invariants, authorship, integration) are unchanged.
- `implementer.md` overrides three `tdd` rules that assume a person at the keyboard: seams come from the spec rather than being confirmed with a user, a slice is one criterion, and there is no refactor step.

## What is given up

The test writer now knows the implementation it is about to write. The commit checks prove each test failed before its code existed and was never weakened afterwards; they do **not** prove the test asserts what the spec means rather than what the builder planned. That judgment is the verifier's check 1 (tests against the spec's own text), as it already was in v8 — which is where v8's only test rework was caught.

## How it is decided

Run v10 on T3 and T2-hard, at most 3 runs each, against v9's numbers: pass^3, hidden-test score, runs, non-cache tokens, rework rounds, interventions. If v10 reaches pass^3 at lower cost, the split has no remaining argument. If it fails where v9 passes, record whether the failure is one the separate test writer would have prevented.
