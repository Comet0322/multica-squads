---
name: multica-artifact-frontend
description: "Frontend artifact submission (Git version). Write the implementation spec to docs/frontend/<ISSUE-KEY>/impl-spec.md in the product repo, push the deploy branch and return the link for review and testing. For @FrontendDev."
version: 3.0.0-repo
metadata:
  upstream:
    - multica-frontend-impl
    - multica-design-ui-impl
  downstream:
    - multica-verification
    - multica-artifact-cicd-sync
---

# Artifact · Frontend (implementation spec lands in the Git repo)

## Purpose

**Only specifies what the frontend implementation spec must contain, how to self-check it, and where it lands.** This team does not use Confluence / JIRA: **the implementation spec lands in `docs/frontend/<ISSUE-KEY>/impl-spec.md` in the product repo** (use the path in the "Artifact paths" table of the repo-root `MULTICA.md`; this default applies only when that table is missing). Do not call `multica-platform-confluence` / `-jira`. The code lives in the same repo; this document is for reviewers / testers / the Leader to check against.

> This skill **contains no scripts**; for coding and experience see `multica-frontend-impl`. `multica-platform-figma` may still be used to read design links when the team uses Figma.

Preconditions: `<ISSUE-KEY>` is the current Issue identifier; get a working copy with `multica repo checkout <url>`; read the repo-root `MULTICA.md` first (BLOCKED if missing); the deploy branch is `release/<ISSUE-KEY>-<slug>` (declared by the Leader at G0; use it if it exists, otherwise create it from `main`). **Never push `main` directly.**

## @FrontendDev standard flow

```text
1. multica-frontend-impl - read upstream (PRD / design / UI / API contract, all files in the repo)
2. Write docs/frontend/<ISSUE-KEY>/impl-spec.md (before starting or updated during implementation)
3. Self-check (see the table below); on FAIL complete the document first
4. git add / commit (docs(frontend): <ISSUE-KEY> vN) -> push the deploy branch
5. Implement pages / components + tests (feature branch feature/<ISSUE-KEY>-fe-<slug> per MULTICA.md)
6. Comment on the Issue to the Leader: impl-spec link, deploy branch, commit SHA, code evidence
```

Link: `<repo web url>/src/branch/release/<ISSUE-KEY>-<slug>/docs/frontend/<ISSUE-KEY>/impl-spec.md`. On re-review update the same file and bump the version in the revision log.

## Implementation spec conventions (self-check before pushing)

| Section | Required | Content requirements |
| --- | --- | --- |
| **Document header** | Yes | Author, time, version, status, links to the Issue, PRD, design, UI and API contract files |
| **Pages and routes** | Yes | Page · route · entry point · AC- |
| **Interaction and states** | Yes | Actions / feedback; **empty / loading / error / no-permission states** |
| **Component mapping** | Yes | UI area · component · reuse / new |
| **API integration** | When involved | API-ID · call timing · error UX |
| **Forms and validation** | When involved | Rules · prompt copy · BR- |
| **Experience and accessibility** | As needed | Responsiveness, keyboard, perceived performance |
| **Mock strategy** | When the backend is not ready | Mock location and switch-over condition |
| **Verification plan** | Yes | Component / manual / E2E · AC- |
| **Revision log** | Yes | Version increments |

## Why this works

It pulls "interaction and states" out of the code into a reviewable document that sits next to the PRD, the design and the API contract in the same repo, so downstream roles read one set of files and never get lost.
