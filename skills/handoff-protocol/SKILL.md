---
name: handoff-protocol
description: The format for briefing work, reporting it, and sending it back; who may change what; and how cycles on one issue stay unambiguous
---

# Handoff protocol

Work moves by **ownership**, not by messages. The spec belongs to `sq-lead`, each ticket to
`sq-reviewer`, each handoff to the agent it is assigned to. An owner briefs and sequences its
own children; everyone else does their one task and finishes it.

**Finishing your own issue IS the handoff.** Set it `done` and the stage barrier wakes your
owner within seconds. Nothing has to be nudged and nothing has to be created to pass work on.

## Who may change what
- **Your own issue**: its status, its `Verdict` and `Head SHA` properties, and comments on it.
- **An owner, on its own children only**: their status (including reopening one), their
  properties, and briefs on them.
- **Never**: another member's issue, a sibling's status, your parent's status or description,
  or an @mention of a peer. Sequencing belongs to one agent per level — two agents promoting
  the same stage will have the same work done twice.

## Briefing (an owner to one of its children)
The brief for the first cycle is the child's **description**, written when the owner creates
it. A brief for any later cycle is a **comment** on that same issue (see "Sending work
back"). Both carry:
- `Spec: <spec-id>`, `Ticket: <ticket-id>`, `Covers: AC#...` (criteria copied verbatim).
- **Goal**: one sentence.
- **Inputs**: files, branch, and the exact prior comments to read.
- **Output**: exactly what to deliver.
- **Verify by**: the command or check that proves it is done.
- **Conventions**: one line pointing at the `Conventions` part of the spec's Impact analysis
  — *not* a copy of it. The spec is the single source, it is cited on the first line, so
  there is nothing to keep in step and nothing to forget to quote. **Whoever receives a brief
  reads that section before starting**, and a convention violation fails review exactly like
  a missing test. On B1 the only real rework cycle existed because two conventions never
  reached the implementer: a compiled binary was committed and error messages lacked the
  required `<tool>: ` prefix.

## Reporting (a child to its owner)
Post a comment on your own issue, @mentioning your owner — the ticket's owner for a handoff
under a ticket, `sq-lead` for one under the spec:
- **Done**: what changed (files, branch, commit SHA).
- **Verified**: the commands you ran and their real output. Pasted output, never a claim.
- **Risks / open questions**.
- **Verdict** (reviewers and QA): APPROVE/CHANGES REQUESTED or PASS/FAIL in the report, and
  set as data before you set the issue `done`:
  `multica issue property set <issue-id> --name Verdict --value "PASS"` and
  `--name "Head SHA" --value <sha>`. The option set is closed, so a paraphrase is rejected
  rather than stored as something nothing can read, and `multica issue property list <id>`
  returns it resolved by name. The prose is the evidence; the property is the decision; the
  SHA is what stops a verdict being read against a tree nobody tested.

Reference acceptance criteria by number (AC1, AC2, ...) from the spec. Keep one task per
handoff and do no work outside your role.

## Sending work back, and keeping cycles straight
Rework reopens the existing issue — the owner sets it back to `todo` with a brief as a
comment. Nothing new is created, so one issue accumulates several briefs and reports, and
**the thread must say which cycle each belongs to**:

- An owner heads a later brief `**Brief (cycle N)**`, N counting from 2.
- Whoever works it heads its report `**Report (cycle N)**` with the same N.
- **The newest brief and the newest report are the only ones in force.** An earlier report
  describes a tree that no longer exists; never act on it, and never answer it.

A cycle-N brief must also say **what has already been ruled out**: which approach was tried,
what it produced, and why it was rejected. The agent receiving it has a fresh context and no
memory of the earlier cycle, so without this it can spend the cycle repeating a failed
attempt — and after two failed cycles on one problem the owner stops looping and sets the
ticket `blocked`.

Fix exactly what the newest brief names. Do not start over, do not widen the change, push to
the same branch, report, and set the issue `done` again. Reopening re-fires the barrier when
it completes, so the owner is woken exactly as it was the first time.

## Status rules (autonomous by default)
No human is in the loop below the spec. Never leave a task waiting for a person to press a
button.
- **Finished your task**, whatever the verdict: post the report, set the `Verdict` property if
  you are a reviewer or QA, then set your own issue `done` (`multica issue status <id> done`).
  A failed review or QA is a *finished* task: the verdict is the deliverable, and your owner
  decides what happens next. Finishing is what wakes your owner.
- **`blocked`**: only for a problem you genuinely cannot resolve (missing access,
  contradictory requirements, an external dependency). Say exactly what is needed and from
  whom. Ambiguity you can resolve by reading the spec or the code is not a block.
- **`in_review`**: only on the spec issue, for a human gate the spec declares. Never as a
  "finished" state — stage barriers fire only on `done`/`cancelled`, so `in_review` stalls
  the pipeline.
- Do not ask the user to confirm routine decisions.

## Working in a repository
- Get the code with `multica repo checkout <url>` (the URL is in the brief's Inputs or
  `multica repo list`), never by editing a local directory by absolute path. It gives you an
  isolated worktree.
- The worktree starts on a throwaway agent branch. Switch to the feature branch named in the
  spec: `git fetch origin && git switch feat/<name>` if it exists on origin, else
  `git switch -c feat/<name> origin/main`. Never commit to main.
- Push to the feature branch (`git push -u origin feat/<name>`) before reporting, so the next
  stage can fetch it. State the branch and commit SHA in your report.
- Reviewers, QA and docs: `git fetch origin` and work from the SHA in the **newest** report on
  the issue you are judging, never from memory and never from an earlier cycle's SHA. Record
  the SHA you actually tested in `Head SHA`.
- Before you push, check what you are committing (`git status`, `git diff --cached --stat`):
  source and tests only. Never a compiled binary, a coverage file, an editor or OS file, or a
  `.gitignore` nobody asked for. Fix the formatting the project uses (for Go, `gofmt -l .`
  must print nothing).
