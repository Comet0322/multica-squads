---
name: forgejo-pr
description: Push a feature branch to the local Forgejo and open a pull request that auto-completes the parent issue on merge
---

# Opening a PR on the local Forgejo

The repo's `origin` already points at the local Forgejo (credentials are embedded in the remote; never print them).

1. Make sure all work is committed on the feature branch, then `git push -u origin <branch>`.
2. Write the PR body to a file. It MUST contain a closing line `Closes <SPEC-ISSUE-IDENTIFIER>` (the id on the handoff's `Spec:` line, e.g. `Closes ACHE-30`; NOT the ticket or handoff id) so merging the PR completes the spec issue automatically. Also include: spec summary, acceptance-criteria evidence table, and the ticket ids with their review and QA verdicts.
3. Open the PR: `/home/comet/Code/multica-squads/tools/forgejo-pr.sh <repo-name> <branch> main "<title>" <body-file>` (prints the PR URL).
4. Post the PR URL as a comment on the spec issue and on the Deliver ticket. Do not merge it: merging is the human gate.
