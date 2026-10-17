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
- **Conventions**: one line pointing at the `Conventions` part of the spec's Impact
  analysis — *not* a copy of it. The spec is the single source and it is already cited on
  the line above, so there is nothing to keep in step and nothing to forget to quote.
  **Whoever receives a handoff must read that section before starting**, and a convention
  violation fails review exactly like a missing test. On B1 the only real rework cycle
  existed solely because two conventions never reached the implementer (a compiled binary
  was committed, and error messages lacked the required `<tool>: ` prefix); copying the list
  into every handoff would have fixed that case while leaving the copying step to forget.

## Reporting (member -> leader)
Post a comment mentioning the leader with:
- **Done**: what changed (files, branch/commit).
- **Verified**: commands run and results.
- **Risks / open questions**.
- **Verdict** (reviewers and QA): APPROVE/CHANGES REQUESTED or PASS/FAIL in the report, AND
  set as data before you set the issue `done`:
  `multica issue property set <issue-id> --name Verdict --value "PASS"` plus
  `--name "Head SHA" --value <sha>`. The option set is closed, so a paraphrase is rejected
  instead of being stored as something nothing can read; `multica issue property list <id>`
  returns it resolved by name. The prose is the evidence; the property is the decision.

Reference acceptance criteria by number (AC1, AC2, ...) from the spec on the parent issue.

**Mention the owner of the level above you, never a peer.** A handoff under a ticket reports
to that ticket's owner, `sq-reviewer`; a handoff under the spec reports to `sq-lead`. A
member never mentions another member and never changes another issue's status: sequencing
belongs to the owner, and two agents promoting the same stage will do the same work twice.

**Finishing your own issue IS the handoff.** Set it `done`; the stage barrier wakes the owner
within seconds. Nobody needs to be nudged, and nothing needs to be created to pass work on.

**Rework arrives as your own issue reopened**, set back to `todo` with a comment naming what
to fix — not as a new issue. Fix exactly that, push to the same branch, report, set `done`.

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
