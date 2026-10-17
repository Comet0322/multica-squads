---
name: forgejo-pr
description: Push a feature branch to the local Forgejo and open a pull request that auto-completes the parent issue on merge
---

# Opening a PR on the local Forgejo

The repo's `origin` already points at the local Forgejo (credentials are embedded in the remote; never print them).

1. Make sure all work is committed on the feature branch, then `git push -u origin <branch>`.
2. Write the PR body to a file. It MUST contain a closing line `Closes <PARENT-ISSUE-IDENTIFIER>` (e.g. `Closes ACHE-30`) so merging the PR completes the parent issue automatically. Also include: spec summary, acceptance-criteria evidence table, links to the review and QA sub-issues.
3. Open the PR: `/home/comet/Code/multica-squads/tools/forgejo-pr.sh <repo-name> <branch> main "<title>" <body-file>` (prints the PR URL).
4. Post the PR URL as a comment on the parent issue. Do not merge it: merging is the human gate.
