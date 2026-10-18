---
name: handoff-protocol
description: The rules every squad agent follows when handing work over — what starts a run, how to restart one, what to write where
---

# Handoff protocol

## Only three things start a run

1. An issue is **created** in a status other than `backlog`.
2. Its **assignee changes** while it is not `backlog`.
3. Its status moves **out of `backlog`** into something that is not `done`/`cancelled`.

Consequences, all measured:

- `done → todo` and `blocked → todo` start **nothing**, and the CLI prints "status changed to todo" anyway. The board looks right with nobody working.
- **Every start and restart is two writes**: `multica issue status <id> backlog`, then `multica issue status <id> todo`.
- **Create every issue `backlog`**, then promote it. `issue create` has no `--no-start`.
- A parent in `backlog`, `done` or `cancelled` receives no stage-barrier notification at all.

## `done` is the only verb you have

- Finishing your own issue (`done`) fires the stage barrier and wakes the issue above you. That is the entire handoff.
- **Never** `@mention` anyone. Never set anything `blocked` — it is not terminal, fires no barrier, and nothing is watching.
- Never change the status of, or comment on, an issue that is neither yours **nor a sub-issue of one you own**. Promoting, briefing and restarting your own children is how an owner works; reaching sideways or upwards is not. **One exception, for one purpose**: a `**Relay**` comment on the spec issue, quoting a person who commented on an issue of yours. Nothing else reaches the leader, and the leader is the only agent allowed to answer a person.
- Cannot finish the work? You still finish the **issue**: say exactly what is wrong in your report and set it `done`. Your owner decides.

## Reporting

- One comment on your own issue, starting `**Report (cycle N)**`. N is 1, or 1 + the number of `**Report` comments already there.
- **Evidence is pasted command output, never a claim.** "Tests pass" without the command and its real output is not evidence.
- State what you did, what you verified, and anything you could not do. No summary of these instructions.

## Your issue tells you everything

Your description carries `Spec: <id>`, `Ticket: <id>`, `Covers: AC#...`.

- **Read the acceptance criteria from the spec issue, never from a copy.** Nothing copies them, so there is nothing to go stale.
- The contract is the spec's description **plus every `**Spec correction**` comment on it**, newest in force.
- Conventions come from the spec's `Impact analysis`.

## Being sent back

A reopen arrives as `backlog` then `todo`, with a `**Brief (cycle N)**` comment on your issue naming what to fix. `N` is 1 + the number of `**Brief` comments already on that issue. Fix only what the brief names.

## Working in a repository

- `multica repo checkout <url>` gives you a worktree — the clone URL is the spec's `Repo` line, which is the only place it is written. Work on the branch the spec names; never commit to `main`.
- **Get onto that branch like this, every time:** `git fetch origin`, then `git checkout -B <branch> origin/<branch>` if it exists on the remote, or `git checkout -b <branch> origin/main` if it does not (you are the first stage of the first ticket). A fresh checkout does not have the branch locally, and a plain `git checkout -b` forks from `main` and silently drops every earlier stage's work. **Never force-push a commit anyone else may have read** — the one exception is your own tip commit, below.
- Commit and push your own stage before you set yourself `done`. Push as `squadbot`; never print a credential.
- **Commit as yourself, every time, with `-c` on the command:**

  ```
  git -c user.name=<your agent name> -c user.email=<your agent name>@multica.local commit -m "<subject>"
  ```

  So `sq-qa` commits as `sq-qa <sq-qa@multica.local>`. Pass it with `-c`, never `git config`: a checkout is a **git worktree** and shares the repository's config, so a `git config` write lands on every other stage too. That shared config is also why this matters — on an unconfigured machine it has produced commits authored as a *person* on a squad branch, which makes a hands-off run look like it was not, and the verifier now rejects a stage for it. Your own name in the author field is what makes each stage's work attributable without a trailer.
- **Before you set yourself `done`, check your own commits' author**: `git log --format='%h %ae' origin/<branch>..HEAD` before you push, or `origin/main..HEAD` when the branch is new. Every one must be your agent name. If any is not, fix it now while it is still the tip and nobody has built on it: `git commit --amend --author="<your agent name> <<your agent name>@multica.local>"` (or `git rebase -i` for more than one), then `git push --force-with-lease`. **This is the only force-push you may ever do**, and it is safe only here: the stages of a ticket run strictly one after another, so your tip is unreviewed and unread. Once the next stage has pushed, the commit is no longer yours to rewrite and the verifier will reject the ticket instead.
- Record the SHA your work ended on in the property your own instructions name.
