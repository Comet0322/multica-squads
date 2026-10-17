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
- Never change the status of an issue that is not yours, and never comment on an issue you do not own.
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

A reopen arrives as `backlog` then `todo`, with a `**Brief (cycle N)**` comment on your issue naming what to fix. Fix only what the brief names.

## Working in a repository

- `multica repo checkout <url>` gives you a worktree. Work on the branch the spec names; never commit to `main`.
- Commit and push your own stage before you set yourself `done`. Push as `squadbot`; never print a credential.
- **Commit with this exact identity, every time:**

  ```
  git -c user.name=squadbot -c user.email=squadbot@localhost commit -m "<subject>" -m "Co-Authored-By: <your agent name> <your-name@multica.local>"
  ```

  Pass it with `-c` on the command, never `git config`, which would write into a config the whole repository shares. A checkout is a **git worktree**, so it inherits that shared config — on an unconfigured machine that has produced commits authored as a *person* on a squad branch, which makes a hands-off run look like it was not. One author for the pusher, the trailer for who actually did the stage.
- Record the SHA your work ended on in the property your own instructions name.
