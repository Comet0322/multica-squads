---
name: flat-protocol
description: Mechanics every dev-flat agent shares: what starts a run, restarts, reports, branches, commit identity. No policy, only platform facts.
---

# dev-flat protocol (mechanics only)

Draft, 2026-11-23. Every line here is a platform fact already measured in `CLAUDE.md` "Hard-won facts"; judgement rules live in each agent's own file.

## What starts a run
- A run starts on an issue only when it is **created** outside `backlog`, its **assignee changes** outside `backlog`, or its status leaves `backlog` for something not `done`/`cancelled`. `done -> todo` and `blocked -> todo` start **nothing**.
- So every start or restart is **two writes**: `multica issue status <id> backlog`, then `... todo`. Create every issue `backlog`, then promote it.
- A person's comment on an agent-assigned issue wakes its assignee. An agent's comment on an agent-assigned issue wakes nobody. Any comment on the squad-assigned spec wakes the leader (the leader's own are suppressed).
- `done` and `cancelled` are the only terminal states. `blocked` fires no barrier and is never used.

## Members have one verb
- Finish your own issue with `done`. That fires the stage barrier and wakes the leader. Never `@mention`, never `blocked`, never comment on or change an issue you do not own.
- One exception: a `**Relay**` comment on the spec, when a person has commented on your issue. It is the only path from a member to the leader.
- If you cannot finish the work, you still finish the **issue**: say exactly what is wrong in the report and set `done`. The leader decides.

## Reports
- One comment on your own issue starting `**Report (cycle N)**`; N = 1 + the number of `**Report` comments already there.
- Evidence is pasted command output. "Tests pass" without the command and its output is not evidence.
- Properties (`Result`, `Red SHA`, `Head SHA`, `Gate`) are set with `multica issue property set <id> --name <Name> --value <v>` and do not appear in the timeline; set them **after** the push, from the commit actually pushed.

## Repository
- `multica repo checkout <clone url>`; the url is on the spec's `Repo` line. Never commit to `main`.
- Get on the branch every time: `git fetch origin`; `git checkout -B <branch> origin/<branch>` if it exists on the remote, otherwise `git checkout -b <branch> origin/main`. If it exists, the issue's `Base SHA` must be an ancestor of it (`git merge-base --is-ancestor`), otherwise stop and report that as a blocker.
- Commit as yourself, with `-c` on the command, and check the author before pushing:
  `git -c user.name=<agent name> -c user.email=<agent name>@multica.local commit -m "<subject>"`, then `git log --format='%an <%ae>' origin/main..HEAD`.
- Never `git config` in a checkout (the worktree shares the repository's config). Never force-push a commit anyone else may have read. Never print a credential.
