---
name: handoff-protocol
description: The format for briefing work, reporting it, and sending it back; which single action wakes the next agent; who may change what; and how cycles on one issue stay unambiguous
---

# Handoff protocol

Work moves by **ownership**, not by messages. The spec belongs to `sq-lead`, each ticket to
`sq-reviewer`, each handoff to the agent it is assigned to. An owner briefs and sequences its
own children; everyone else does their one task and finishes it.

**Finishing your own issue IS the handoff.** Set it `done` and the stage barrier wakes your
owner within seconds. Nothing has to be nudged and nothing has to be created to pass work on.

## One event, one wake — and only three things start a run

Nothing here runs on a timer, so every step forward is exactly one wake. A second wake for
the same event is a hazard, not a safety net: two runs read the same state and both promote
the stage or both open the same rework. A *missing* wake is worse, and it is silent.

A run begins on an issue in exactly three ways (`service/issue_trigger.go:126-141`, the one
predicate both write paths use):
1. the issue is **created** in any status other than `backlog`,
2. its **assignee changes** while it is not in `backlog`,
3. its status moves **out of `backlog`** into something that is not `done`/`cancelled`.

Nothing else does. In particular **`done → todo` and `blocked → todo` start nothing**, and
`multica issue status` still prints "status changed to todo", so the board looks right while
no one is working. A comment you write on an issue assigned to another *agent* also starts
nothing unless it carries an explicit mention link.

What follows from that:
- **Finishing** (`done`) wakes your owner through the stage barrier. **Do not @mention your
  owner in your report.** The mention wakes it on your issue and the barrier wakes it on the
  parent about a second later; the two are different issues, so the platform does not
  deduplicate them. In B1, 18 of 74 runs started within 3 s of a comment for exactly this
  reason.
- **Starting or restarting a child** — a first promotion, a rework, an answer to a blocked
  child, a stage that must run again — is always the same two writes, in this order:
  ```
  multica issue status <id> backlog      # from done/todo/in_progress/blocked: starts nothing
  multica issue status <id> todo         # out of backlog: THIS is the wake
  ```
  Any brief goes in a comment **before** the first write, with no mention. Reopening with a
  single `status <id> todo` from `done` is the most dangerous mistake available here.
- **Waking an agent you cannot restart** — your owner, or a peer you may not touch — only
  ever happens for an escalation, and only through a mention link in the roster form
  `[@Name](mention://agent/<agent-id>)`. A plain `@name` is dead text that parses as nothing.
- Do not `rerun` an issue you have just commented on **when that comment can wake its owner
  by itself** — a comment on the squad-assigned spec issue, or any comment carrying a mention.
  On an agent-assigned handoff a plain comment wakes nobody, so a comment plus a restart is
  exactly one wake.

## Who may change what
- **Your own issue**: its status, its `Verdict` and `Head SHA` properties, and comments on it.
- **An owner, on its own children only**: their status (including reopening one), their
  properties, and briefs on them.
- **Never**: another member's issue, a sibling's status, your parent's status or description,
  or an @mention of a peer. Sequencing belongs to one agent per level.

## Briefing (an owner to one of its children)
Create every child `backlog`, then promote the first stage out of it — creating an issue in
any other status starts a run immediately and `issue create` has no `--no-start`, while a
child parked in `backlog` is inert until it is promoted.

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
Post a comment on your own issue — **with no @mention**; finishing it is what wakes your
owner:
- **Done**: what changed (files, branch, commit SHA).
- **Verified**: the commands you ran and their real output. Pasted output, never a claim.
- **Risks / open questions**.
- **Verdict** (reviewers and QA): in the report, and set as data before you set the issue
  `done`:
  `multica issue property set <issue-id> --name "QA verdict" --value "PASS"` (QA; a ticket's
  owner uses `--name "Review verdict" --value "APPROVE"` on the child it judged) and
  `--name "Head SHA" --value <sha>`. There are two separate properties on purpose, each with
  a closed two-value option set, so the platform itself rejects a verdict written by the wrong
  role instead of leaving prose to police it. `multica issue property list <id>` returns both
  resolved by name. The prose is the evidence; the property is the decision; the SHA is what
  stops a verdict being read against a tree nobody tested.

Reference acceptance criteria by number (AC1, AC2, ...) from the spec. Keep one task per
handoff and do no work outside your role.

## Escalating (the one case where you @mention)
`blocked` is **not** a terminal status, so it fires no stage barrier and wakes nobody. A
`blocked` issue with nothing else done is a permanent stall — there is no recovery utility in
this squad.

So escalation is two actions, in this order:
1. Post a comment **on your own issue** mentioning your owner in the roster link form
   (`sq-reviewer` for a handoff under a ticket, `sq-lead` for a ticket or a handoff under the
   spec), stating what you tried, what is still wrong and exactly what you need decided.
2. `multica issue status <your-id> blocked`.

The mention is the wake (measured: a mention in a comment woke `sq-lead` on an issue assigned
to someone else), and it is the only one — so if you set `blocked` without it, nothing
anywhere will notice. Your owner answers in a comment and then restarts you with the two
writes above; it cannot reach you any other way. Use `blocked` only for a problem you genuinely cannot resolve — missing
access, contradictory requirements, an external dependency, or two failed cycles on one
problem. Ambiguity you can resolve by reading the spec or the code is not a block.

## Sending work back, and keeping cycles straight
Rework reopens the existing issue — the owner posts the brief as a comment, then restarts it
with the two writes above. Nothing new is created, so one issue accumulates several briefs and
reports, and **the thread must say which cycle each belongs to**:

- An owner heads a later brief `**Brief (cycle N)**`. **N is 1 + the number of comments on
  this issue that already begin `**Brief (cycle`** — count them, never guess, because your
  context is fresh and the thread is the only record.
- Whoever works it heads its report `**Report (cycle N)**` with the same N as the brief it is
  answering. A judgment posted on a *ticket* (a review of one of its children) is headed the
  same way, with the cycle of the child it judged.
- **The newest brief and the newest report are the only ones in force.** An earlier report
  describes a tree that no longer exists; never act on it, and never answer it.

A cycle-N brief must also say **what has already been ruled out**: which approach was tried,
what it produced, and why it was rejected. The agent receiving it has a fresh context and no
memory of the earlier cycle, so without this it can spend the cycle repeating a failed
attempt — and after two failed cycles on one problem the owner stops looping and escalates.

**Reopening a stage invalidates the stages above it, so reset them.** When an owner reopens
stage *k*, every stage above *k* that is already `done` goes back to `backlog` —
`multica issue status <id> backlog`, which starts nothing. The one exception is a stage whose
output cannot be produced twice, an already-open pull request above all: leave it `done` and
say so, or the next barrier will tell its owner to promote it and a second PR gets opened.
Two reasons for the reset, both measured: a later wake works
out what happened from the stage layout, and a stage left `done` makes it read work as
finished that is about to be redone; and the verdict property on that stage is still the old
one, because a property only ever holds its final value and never appears in the timeline.

Only one stage is ever restarted at a time. A stage that completes while a **lower** stage is
still open closes no barrier and wakes nobody, so promote the next one on the wake the first
one gives you, exactly as on the first pass.

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
- **`blocked`**: see "Escalating" — the comment with the @mention comes first.
- **`in_review`**: only on the spec issue, for a human gate the spec declares. Never as a
  "finished" state — stage barriers fire only on `done`/`cancelled`, so `in_review` stalls
  the pipeline.
- A parent in `backlog`, `done` or `cancelled` receives **no** child-done notification at
  all, so never leave work running under a parent in one of those states.
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
