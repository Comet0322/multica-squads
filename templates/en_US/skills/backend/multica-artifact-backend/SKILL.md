---
name: multica-artifact-backend
description: Backend artifact submission (Git version). Write the API contract to docs/backend/<ISSUE-KEY>/api-contract.md in the product repo, push the deploy branch and return the link for frontend / test consumption. Used by @BackendDev.
version: 3.0.0-repo
---

# Artifact · Backend (contract lands in the Git repo)

This team does not use Confluence / JIRA / Apifox. **The only place an API contract lands is `docs/backend/<ISSUE-KEY>/api-contract.md` in the product repo** (put an OpenAPI file next to it as `openapi.json` if you have one). Do not call `multica-platform-confluence` / `-jira` / `-apifox`.

Preconditions: `<ISSUE-KEY>` is the current Issue identifier; get a working copy with `multica repo checkout <url>`; read the repo-root `MULTICA.md` first (BLOCKED if missing); the deploy branch is `release/<ISSUE-KEY>-<slug>` (declared by the Leader at G0; use it if it exists, otherwise create it from `main`). **Never push `main` directly.** Artifact paths come from the "Artifact paths" table in the repo-root `MULTICA.md`; use this skill's default path only when that table is missing.

## Flow

```text
1. Read upstream: PRD (docs/prd/<ISSUE-KEY>.md) and the design if present (docs/design/<ISSUE-KEY>/design.md)
2. Write docs/backend/<ISSUE-KEY>/api-contract.md (header, overview, endpoint list with API-ID / method / path / BR- / AC-, endpoint details with schemas / error codes / auth, data model if affected, TDD mapping API-ID -> unit tests, revision log)
3. Self-check; on FAIL fix the draft first
4. git add / commit (docs(api): <ISSUE-KEY> vN) -> push the deploy branch
5. Comment on the Issue to the Leader: contract link, deploy branch, commit SHA, version
```

Link: `<repo web url>/src/branch/release/<ISSUE-KEY>-<slug>/docs/backend/<ISSUE-KEY>/api-contract.md`. This stage produces only the contract; the Leader dispatches server-side implementation (`multica-backend-impl`) after the contract passes both gates. On re-review update the same file; a breaking change bumps the version and notifies the Leader and @FrontendDev.
