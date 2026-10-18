---
name: forgejo-pr
description: Push a feature branch to the local Forgejo and open a pull request that completes the spec issue on merge
---

# Opening a PR on the local Forgejo

`origin` already points at the local Forgejo and the push credential comes from the machine's git credential store: you push as `squadbot`, never as a person. `main` is protected — a direct push is rejected by the server and only a human can merge. Never print a credential.

1. Confirm everything is committed and pushed: `git push -u origin <branch>`.
2. Write the PR body to a file. Its **first line** must be:

   `**Review comments must go on <SPEC-ISSUE-ID>. Comments on this pull request are never read.**`

   That is not a courtesy — the platform's webhook models only `pull_request` and `ci_status`, so a review left here reaches nobody and the human waits forever believing they replied. Then `Closes <SPEC-ISSUE-ID>` (the spec, not a ticket) so merging completes the spec. Then: what changed, one row per `AC#`/`I#` **that is still live** with the test that covers it, every ticket id with its `Result`, and any `Risks` line from a ticket's report quoted verbatim — the PR body is the only place a human ever sees one. **Leave out every number a `**Spec correction**` retired** and say in one line which were retired and which ticket acted on it: a retired criterion's row would cite a test that has been deleted.
3. **Try the update first, always**: `tools/forgejo-pr.sh --update <repo-name> <branch> <body-file>`. If a PR is open it rewrites the body and prints the URL — go to 5. If none is open it says `no open PR with head '<branch>'` and changes nothing; then create it. If one is open, skip to 4. Otherwise `tools/forgejo-pr.sh <repo-name> <branch> main "<title>" <body-file>` — prints the PR URL.
4. Update-first is the order because the only other record of an open PR is the URL in your own `**Status**` comment, which you write *after* opening one — so a run that opened a PR and died leaves no record, and a create would fail with a non-zero exit that reads like a broken step. Rebuild the whole body from the ticket reports every time you update: later commits reach an open PR by themselves, but its body does not, so a criterion added after it was opened is invisible to the human until you do this.
5. Never merge it. Merging is the human gate.
