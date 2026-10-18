---
name: multica-handoff-protocol
description: Handoff protocol for members (non-Leader) after finishing a task - how to deliver, do not mention the Leader, who may change the status, and what to do when sent back. Shared by all members of reviewed squads; do not repeat it in each agent's instructions.
---

# Handoff Protocol (shared by members)

This skill applies to squads such as `software-development-reviewed`, where the Leader dispatches work with @mention. The Leader is the only gate-keeper and the only dispatcher.

## What to do when you finish

1. Confirm your artifact has been pushed to the branch specified at dispatch (never push `main` directly).
2. Leave **one** delivery comment on the dispatched issue. It must start with `**Delivery**` and include:
   - Branch name and commit SHA (the SHA after pushing).
   - List of changed files.
   - A point-by-point comparison with the acceptance criteria (AC).
   - The verification commands you actually ran and their **complete output**. "Tests pass" without the pasted output is not evidence.
   - Known limitations and anything you could not do.
3. Write the comment to the Leader in plain text (e.g. start with `**Delivery**` and say "Leader, please decide the gate" in the body). **Do not** write any mention links.

## Do not @mention the Leader

The Leader does not need to be mentioned to wake up: as soon as you leave a comment on this issue, the platform automatically calls the Leader to evaluate.

- **Do not** write links such as `[@Leader](mention://agent/<id>)` in the comment. You do not have the Leader's id; an invented link points to a non-existent agent and the Leader never receives your delivery (observed in TEST-11: the Architect made up an id and the delivery sat on the issue with nobody picking it up).
- To address the Leader, just write the plain text "Leader".
- The same applies to other members: you do not dispatch work, so you do not need to mention anyone.

## How the status changes

- After finishing, **do not** set the issue to `done` or `in_review` yourself. Those two statuses are decided by the Leader after the gate decision.
- You are only responsible for the delivery comment (plain text, no mention links).

## When you cannot finish

- Likewise leave a comment on the issue (plain text, no mention links) starting with `**Blocked**`, explaining what is missing, why it is needed, and who can provide it.
- Do not set the status to `blocked`, and do not cancel the task yourself.

## What not to do

- Do not @ other members; all dispatching goes through the Leader only.
- Do not change the status of issues you are not responsible for, and do not comment on them.
- Do not announce "checks passed"; the authority to decide the gate belongs to the Leader alone.

## Commit identity

Every commit must use your own identity, specified on the command line with `-c`; do not write it with `git config`:

```
git -c user.name=<your agent name> -c user.email=<your agent name>@multica.local commit -m "<subject>"
```

Check the author before pushing, not at the very end:

```
git log --format='%h %ae' origin/<branch>..HEAD
```

If the author is wrong, fix it and then push.

## When sent back

When the Leader sends work back, it leaves a comment on the issue listing the items to fix (`**Rework**`).

- Fix only the items listed in the comment; do not widen the scope.
- After fixing, deliver again following "What to do when you finish".
