---
name: multica-test-orchestration
description: Tester T1/T2/T3 orchestration and gates (Git version). Cases, coverage assessment and the test report are written to docs/test/<ISSUE-KEY>/ in the product repo and automation lands in the repo; no JIRA / Confluence / XMind / Apifox. Preferred skill for @Tester.
version: 2.0.0-repo
---

# Test Orchestration (acceptance verifier, Git version)

You are accountable for "was the requirement actually implemented". Testing shifts left in **T1 / T2 / T3**. This team does not use JIRA / Confluence / XMind / Apifox: ignore the platform steps (fetch requirements, publish, import, batch run) in `multica-test-t1-design`, `multica-test-t2-coverage` and `multica-test-t3-api-automation`, and follow the Git flow below. Their case templates, traceability method and coverage self-check remain usable.

## Preconditions

- `<ISSUE-KEY>` is the current Issue identifier; get a working copy with `multica repo checkout <url>`; read the repo-root `MULTICA.md` first (BLOCKED if missing).
- Deploy branch = `release/<ISSUE-KEY>-<slug>` (declared by the Leader at G0). Commit automation to the branch the Leader names; **never push `main` directly**.
- Artifact paths follow the "Artifact paths" table in `MULTICA.md`: cases at `docs/test/<ISSUE-KEY>/t1-cases.md`.
- Requirement sources: `docs/prd/<ISSUE-KEY>.md` (numbered AC-), design `docs/design/<ISSUE-KEY>/design.md`, contract `docs/backend/<ISSUE-KEY>/api-contract.md`. Do not go to Jira.

## T1: functional cases (once design is ready, parallel with the API contract)

1. Read the PRD's AC- and the design; build an AC <-> case traceability table.
2. Write `docs/test/<ISSUE-KEY>/t1-cases.md`: each case has an id (TC-n), the AC- it covers, preconditions, steps, expected result, priority; each AC- gets at least one positive and one negative / boundary case.
3. Self-check: every AC- has a case; no case is untraceable; expected results are observable and decidable.
4. Commit (`docs(test): <ISSUE-KEY> t1 vN`), push, and comment the link, SHA, version and AC coverage summary on the Issue.
5. No XMind, no import into any case platform.

## Parallel: API cases (once the contract is ready, parallel with implementation)

- From `api-contract.md`, turn every endpoint and error scenario into an **executable acceptance test** under `server/tests/acceptance/<ISSUE-KEY>.test.ts` (path per `MULTICA.md` section 2; backend uses Fastify `inject`, no real port).
- Start each test name with the AC sub-clause id for traceability; assertions must really verify behavior, **no empty or always-true assertions**.
- These tests may be red until the implementation lands; that is normal. Push to the branch the Leader names, return the link, and do not touch implementation code.

## T2: coverage assessment (after G2 PASS, before T3)

- Compare the implementation diff and the contract against T1 and API cases for AC- coverage, list gaps and add cases.
- Write `docs/test/<ISSUE-KEY>/t2-coverage.md`: coverage table (AC- -> case -> status), gaps, added cases.
- The conclusion is only "assessment complete" or "assessment BLOCKED"; never write an acceptance PASS / FAIL.

## T3: execution and test report (after G2.5)

- With a deploy URL and G2.5 PASS: run against the deployed environment.
- When the Leader rules G2.5 N/A (no CI / no deploy environment): degrade per `squad.md` to **real local execution** (`npm --prefix server test`, including acceptance tests), state "executed locally, not verified on a deploy environment" prominently, and cap the verdict at "PASS (local)".
- Write `docs/test/<ISSUE-KEY>/t3-report.md`: commands and **full output**, per-AC result (PASS / FAIL / BLOCKED), for each FAIL the repro steps / expected / actual / evidence / severity, and known limits.
- The overall verdict is exactly one of PASS (local or deployed) / FAIL / BLOCKED.

## Gates (non-negotiable)

- Never pass because it compiles, unit tests pass, or the implementer says it is fine.
- Never turn BLOCKED into PASS.
- Missing material (PRD / contract / implementation SHA) -> stop, list what is missing in an Issue comment and wait for a human or the Leader; never invent it.
- Do not modify implementation code; report defects only.
- Delivery, blocked and handoff follow the `multica-handoff-protocol` skill.
