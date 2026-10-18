---
name: multica-artifact-architect
description: Architect artifact submission (Git version). Self-check the design draft, write it to docs/design/<ISSUE-KEY>/design.md in the product repo, push the deploy branch and return the link. Used by @Architect.
version: 3.0.0-repo
---

# Artifact · Architect (design lands in the Git repo)

This team does not use Confluence / JIRA. **The only place a design lands is `docs/design/<ISSUE-KEY>/design.md` in the product repo.** Do not call `multica-platform-confluence` / `multica-platform-jira`, and do not report BLOCKED because their credentials are missing.

Preconditions: `<ISSUE-KEY>` is the current Issue identifier; get a working copy with `multica repo checkout <url>`; read the repo-root `MULTICA.md` first (BLOCKED if missing); the deploy branch is `release/<ISSUE-KEY>-<slug>` (declared by the Leader at G0; use it if it exists, otherwise create it from `main`). **Never push `main` directly.** Artifact paths come from the "Artifact paths" table in the repo-root `MULTICA.md`; use this skill's default path only when that table is missing.

## Flow

```text
1. multica-technical-design: write docs/design/<ISSUE-KEY>/design.md
2. Self-check against the Chinese skill's section table (header, understanding, non-goals, proposed change, affected components, implementation steps, verification plan, traceability, risks, revision log); on FAIL fix the draft first
3. git add / commit (docs(design): <ISSUE-KEY> vN) -> push the deploy branch
4. Comment on the Issue to the Leader: design link, deploy branch, commit SHA, version
```

Link: `<repo web url>/src/branch/release/<ISSUE-KEY>-<slug>/docs/design/<ISSUE-KEY>/design.md`. On re-review update the same file, bump the version, answer each ArchReviewer REV-n in "review response"; never create a second design file.
