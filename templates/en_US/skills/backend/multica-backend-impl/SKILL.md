---
name: multica-backend-impl
description: "Backend implementation (Git version): read the Issue, PRD and design from the product repo, then drive API and server-side coding with TDD. For @BackendDev: contract first, unit tests, integration verification."
version: 2.0.0-repo
metadata:
  upstream:
    - multica-artifact-architect
  downstream:
    - multica-artifact-backend
    - multica-artifact-cicd-sync
---

# Backend Implementation

## Purpose

Within the approved technical design and Issue scope, deliver the backend implementation with **contract first + TDD**.

> Division of labor with `multica-artifact-backend`: **backend-impl covers how to read upstream and how to write code and tests; artifact-backend covers the API contract document conventions and where it lands (the product repo)**.

## Platform collaboration

This team does not use Confluence / JIRA. Upstream artifacts are read as **files in the product repo** (paths come from the "Artifact paths" table of the repo-root `MULTICA.md`); no platform skill is needed to read them. Publishing the contract goes through `multica-artifact-backend` (a commit on the deploy branch).

## Before you start: read upstream (mandatory)

| Order | Source | How |
| --- | --- | --- |
| 1 | Issue / acceptance criteria | The Issue itself (`multica issue get <ISSUE-KEY>`), including linked Issues named in it |
| 2 | **Related Issues** (relates / dependencies) | Read every Issue the description links to; follow their artifact links as well |
| 3 | PRD / requirement body | `docs/prd/<ISSUE-KEY>.md` on the deploy branch |
| 4 | Architecture design | `docs/design/<ISSUE-KEY>/design.md` on the deploy branch (or the link in the Leader's dispatch) |
| 5 | Existing code | codegraph / targeted reading; follow project conventions |

Insufficient information -> **BLOCKED**; write the open questions down and never guess the shape of an interface.

## Before G2: unit tests (hard gate)

**Before merging into the deploy branch**, you must run **all** unit tests to green locally (or in the project's standard dev container):

```text
1. Run the project's unit test command (e.g. mvn test / npm test / pytest tests/unit)
2. Must be 0 failures; existing tests must not break because of this change (no regression)
3. New / changed APIs must have matching unit tests (Red-Green-Refactor)
4. On failure -> fix it yourself and rerun until fully green
5. Only if it truly cannot run locally (missing dependency / hardware) -> BLOCKED and list the environment gap; never push and "wait for CI to see"
```

**Forbidden**: leaving unit test failures to be discovered by Jenkins / CICD; deleting or skipping existing tests just to get green (unless the Architect / Leader cuts scope in writing).

CI is a **second confirmation**, not the first place unit tests get run.

## TDD flow (core)

```text
1. Read AC- / the architecture's "implementation steps (backend)" -> list API-IDs and behaviors
2. Write / update api-contract.md (hand it to multica-artifact-backend to commit and push, so the frontend can work in parallel)
3. Red      - write failing unit tests (business logic, boundaries, exceptions)
4. Green    - minimal implementation that makes the tests pass
5. Refactor - keep tests green, do not expand scope
6. Integration verification - run the project's commands and paste the evidence
```

**Rules**:

- Business logic must have **unit tests**; even plain CRUD needs coverage of exception branches and boundaries.
- Change the contract document before the implementation; a breaking change must bump the version and notify the Leader / @FrontendDev.
- Never silently change field names or semantics; any deviation from the Architect's design must be explained.

## Coding rules

1. Read before you edit; follow the existing layering and naming.
2. Stay focused on scope; no unrelated refactoring.
3. Error handling: timeouts, idempotency and concurrency are implemented as designed.
4. Report **rerunnable** commands and their results.

## Completion evidence

- API contract link on the deploy branch (`multica-artifact-backend`)
- List of changed files
- **Unit tests**: command + **all-green** result (already passing **before** merging into the deploy branch; 0 failures, no test regression)
- Integration tests (if the project requires them): command + result
- Traceability to API-ID / AC-
- Known limitations

## Mount order (@BackendDev)

```text
multica-backend-impl -> multica-artifact-backend
```

## Why this works

The contract committed in the repo lets the frontend and T1 run in parallel; TDD locks the acceptance criteria into tests up front, reducing rework when G2 merges.
