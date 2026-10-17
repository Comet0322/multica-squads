---
name: forgejo-pr
description: Push a feature branch to the local Forgejo and open a pull request that auto-completes the parent issue on merge
---

# Opening a PR on the local Forgejo

The repo's `origin` already points at the local Forgejo and the push credential is supplied by the machine's git credential store: you push as the `squadbot` account, never as a person. `main` is a protected branch — a direct push to it is rejected by the server, and only a human can merge the PR. Never print or echo a credential.

1. Make sure all work is committed on the feature branch, then `git push -u origin <branch>`.
2. Write the PR body to a file. It MUST contain a closing line `Closes <SPEC-ISSUE-IDENTIFIER>` (the id on the handoff's `Spec:` line, e.g. `Closes ACHE-30`; NOT the ticket or handoff id) so merging the PR completes the spec issue automatically. Also include: spec summary, acceptance-criteria evidence table, and the ticket ids with their review and QA verdicts.
3. Open the PR: `/home/comet/Code/multica-squads/tools/forgejo-pr.sh <repo-name> <branch> main "<title>" <body-file>` (prints the PR URL).
4. Post the PR URL in your report **on your own handoff issue only**. Do not comment on the spec issue or on the ticket: the spec is assigned to the squad, so an agent comment there wakes the leader on top of the stage barrier that is about to wake it anyway, and two leader runs on one state can act twice. The ticket's owner carries the URL into its summary and the leader into the spec's Status comment. Do not merge it: merging is the human gate.
