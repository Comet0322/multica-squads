---
name: multica-pm-artifact-publish
description: PRD landing (Git version). Write the PRD to docs/prd/<ISSUE-KEY>.md in the product repo, push it to the deploy branch and return the file link. Used by @ProductManager for the first submission and for re-submission after review.
version: 3.0.0-repo
---

# PM Artifact Publish (PRD lands in the Git repo)

This team does not use Confluence / JIRA. **The only place a PRD lands is `docs/prd/<ISSUE-KEY>.md` in the product repo.** Do not call `multica-platform-confluence` / `multica-platform-jira`, and do not report BLOCKED because their credentials are missing.

> Content structure belongs to `multica-pm-requirement-spec`; this skill only decides where to submit and how to update.

## Preconditions

- `<ISSUE-KEY>` = identifier of the current Multica Issue (e.g. `TES-1`).
- Target repo = the repo attached to the Issue's project; get a working copy with `multica repo checkout <url>`.
- Read the repo-root `MULTICA.md` first; BLOCKED if it is missing.
- Deploy branch = `release/<ISSUE-KEY>-<slug>` (lowercase English, hyphenated). Create it from `main` if it does not exist. **Never push `main` directly** (protected). Artifact paths come from the "Artifact paths" table in the repo-root `MULTICA.md`; use this skill's default path only when that table is missing.

## Workflow A: first submission

1. On the deploy branch write `docs/prd/<ISSUE-KEY>.md` (the output of `multica-pm-requirement-spec`, with revision log v1 and the OP- list).
2. `git add docs/prd/<ISSUE-KEY>.md && git commit -m "docs(prd): <ISSUE-KEY> v1"`, then `git push -u origin release/<ISSUE-KEY>-<slug>`.
3. Report to the Leader in an Issue comment:
   - PRD link: `<repo web url>/src/branch/release/<ISSUE-KEY>-<slug>/docs/prd/<ISSUE-KEY>.md`
   - deploy branch name, commit SHA, revision v1
   - number of open OP- items

## Workflow B: re-submission after review

- **Update the same file**, bump the revision number, and write "review round N revision" in the summary. **Do not create a second PRD file.**
- Commit as `docs(prd): <ISSUE-KEY> vN`, push the same deploy branch, and report the new SHA and revision so ProductReviewer can re-review.

## Checklist

- [ ] PRD contains G-/FR-/BR-/AC-/OP-/RISK- and a revision log
- [ ] File path is `docs/prd/<ISSUE-KEY>.md`
- [ ] Pushed to the deploy branch, `main` untouched
- [ ] Reported link + SHA + revision
- [ ] Push failed (permission / network) -> BLOCKED with the raw error; do not switch to another landing place
