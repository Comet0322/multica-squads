---
name: multica-frontend-impl
description: "Frontend implementation (Git version): read the Issue, PRD, design, UI and API contract from the product repo, then build the interface with a focus on interaction and experience. For @FrontendDev: component implementation, state handling, integration verification."
version: 2.0.0-repo
metadata:
  upstream:
    - multica-design-ui-impl
  downstream:
    - multica-artifact-frontend
    - multica-verification
---

# Frontend Implementation

## Purpose

Within the confirmed design and Issue scope, turn **UI / interaction / experience** into a working interface and wire it correctly to the API.

> Division of labor with `multica-artifact-frontend`: **frontend-impl covers how to read upstream and how to write components and experience; artifact-frontend covers the implementation-spec document conventions and where it lands (the product repo)**.

## Platform collaboration

This team does not use Confluence / JIRA. Upstream artifacts are read as **files in the product repo** (paths from the "Artifact paths" table of the repo-root `MULTICA.md`). Only the UI design may still live on `multica-platform-figma` when the team uses Figma. Publishing the impl-spec goes through `multica-artifact-frontend` (a commit on the deploy branch).

## Before you start: read upstream (mandatory)

| Order | Source | How |
| --- | --- | --- |
| 1 | Issue / acceptance criteria | The Issue itself (`multica issue get <ISSUE-KEY>`) |
| 2 | PRD | `docs/prd/<ISSUE-KEY>.md` on the deploy branch |
| 3 | Architecture design | `docs/design/<ISSUE-KEY>/design.md` on the deploy branch (or the link in the Leader's dispatch) |
| 4 | UI design | Link from @Designer's `multica-design-ui-impl` |
| 5 | API contract | `docs/backend/<ISSUE-KEY>/api-contract.md` from @BackendDev's `multica-artifact-backend` |
| 6 | Existing frontend code | Targeted reading / codegraph |

Contract or UI missing -> **mock first** and record the mock strategy; unclear interface semantics -> **BLOCKED**, never invent an API.

## Experience-first flow (core)

```text
1. Read AC- / UI / the architecture's "implementation steps (frontend)" -> list pages and state machines
2. Write / update impl-spec.md (hand it to multica-artifact-frontend to commit and push; optional but recommended)
3. Implement by state: default -> loading -> empty -> error -> no permission
4. Interaction: immediate feedback, duplicate-submit protection, understandable error copy
5. API integration: follow the contract strictly; write error branches and retry UX into the impl-spec
6. Component / interaction tests + manual walkthrough of the critical paths
7. Paste rerunnable verification evidence
```

**Rules**:

- **Interaction and experience** have the same priority as functionality: never do only the happy path.
- Never change the API contract; send problems back to @BackendDev.
- Responsive layout / accessibility follow the project baseline; at minimum the main flow must be keyboard-operable.
- No unrelated refactoring; gatekeeping is done by the Leader rerunning `multica-verification`.

## Coding rules

1. Read the UI and the contract before writing components.
2. Single-responsibility components; reuse the design system.
3. When the backend is not ready, use a mock; once the contract is ready, switch over and delete the temporary mock.
4. Report changed files + commands + results.

## Completion evidence

- Frontend implementation-spec link on the deploy branch (if written)
- Page / component code + tests
- Mock notes (if a mock was used)
- Traceability to AC- / API-ID
- Known issues

## Mount order (@FrontendDev)

```text
multica-frontend-impl -> multica-artifact-frontend
```

## Why this works

Experience and state completeness are the easiest things to miss in the frontend; the impl-spec lives next to the PRD, design and contract under `docs/`, so review and testing can work from the same files.
