---
name: forgejo-pr
description: Push a feature branch to the local Forgejo and open a pull request that completes the spec issue on merge
---

# Opening a PR on the local Forgejo

`origin` already points at the local Forgejo and the push credential comes from the machine's git credential store: you push as `squadbot`, never as a person. `main` is protected — a direct push is rejected by the server and only a human can merge. Never print a credential.

1. Confirm everything is committed and pushed: `git push -u origin <branch>`.
2. Write the PR body to a file. It MUST contain `Closes <SPEC-ISSUE-ID>` (the spec, not a ticket) so merging completes the spec. Include: what changed, one row per AC with the test that covers it, and every ticket id with its `Result`.
3. `tools/forgejo-pr.sh <repo-name> <branch> main "<title>" <body-file>` — prints the PR URL.
4. Never merge it. Merging is the human gate.
