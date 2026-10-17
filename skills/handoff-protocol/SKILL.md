---
name: handoff-protocol
description: Standard format for delegating work and reporting results between squad members
---

# Handoff protocol

## Delegating (leader -> member)
Post an issue comment mentioning the member with:
- **Goal**: one sentence.
- **Inputs**: files, branches, prior comments to read.
- **Output**: exactly what to deliver.
- **Verify by**: the command or check that proves it is done.
- **Conventions**: how this project does things, copied from the spec's Impact analysis —
  the error-message shape, what must not be committed, formatting, which dependencies are
  allowed. The receiver has a fresh context and no memory of the project, so a convention
  you leave out is one it cannot know. This field is not optional: on B1 the only real
  rework cycle existed solely because two conventions were never transmitted (a compiled
  binary was committed, and error messages lacked the required `<tool>: ` prefix).

## Reporting (member -> leader)
Post a comment mentioning the leader with:
- **Done**: what changed (files, branch/commit).
- **Verified**: commands run and results.
- **Risks / open questions**.
- **Verdict** (reviewers and QA): APPROVE/CHANGES REQUESTED or PASS/FAIL.

Reference acceptance criteria by number (AC1, AC2, ...) from the spec on the parent issue. Mention only the leader in a report, never another member: peer-to-peer mentions bypass the leader's supervision.

Keep one task per handoff. Do not do work outside your role.

## Status rules (autonomous by default)
Humans are not part of the loop unless the spec says so. Never leave a task waiting for a person to press a button.

- **Finished your task** (whatever the verdict): post the report, then set your own sub-issue to `done` yourself: `multica issue status <id> done`. A failed review or QA is still a finished task; the verdict goes in the comment and the leader creates rework. Finishing is what wakes the leader to start the next stage.
- **`blocked`**: only when you hit a problem you genuinely cannot resolve yourself (missing access, contradictory requirements, an external dependency). Say exactly what is needed and from whom. Try to solve it first; ambiguity you can resolve by reading the spec or code is not a block.
- **`in_review`**: only when the spec or issue explicitly says a human must approve before work continues. Never use it as a "finished" state.
- Do not ask the user for confirmation of routine decisions.

## Working in a repository
- Get the code with `multica repo checkout <url>` (the URL is in the ticket Inputs or `multica repo list`), never by editing someone's local directory by absolute path. It gives you an isolated worktree.
- The worktree starts on a throwaway agent branch. Switch to the feature branch named in the spec: `git fetch origin && git switch feat/<name>` if it exists on origin, else `git switch -c feat/<name> origin/main`. Never commit to main.
- Push your work to the feature branch (`git push -u origin feat/<name>`) before reporting, so the next stage can fetch it. Say the branch and commit SHA in your report.
- Reviewers, QA and docs: fetch the same branch and work from the SHA given in the handoff, not from memory.
- Before you push, check what you are committing (`git status`, `git diff --cached --stat`): source and tests only. Never a compiled binary, a coverage file, an editor or OS file, or a `.gitignore` nobody asked for. Fix the formatting the project uses (for Go, `gofmt -l .` must print nothing).
