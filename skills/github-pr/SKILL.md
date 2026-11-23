---
name: github-pr
description: Push a feature branch to GitHub and open a pull request that completes the spec issue on merge
---

# Opening a PR on GitHub

`origin` already points at the GitHub repo and the push credential comes from the machine's git/`gh` login. `main` is protected by a branch-protection rule — a direct push is rejected by GitHub and only a human merges. Never print a credential.

1. Get a worktree if this wake has none — `multica repo checkout <the spec's clone URL>` — then confirm the branch is on the remote and carries the head you expect: `git fetch origin && git rev-parse origin/<branch>`. **Do not push.** Every stage pushed its own work, you may have no worktree on this wake, and `git push -u origin <branch>` from one that never created the branch locally fails outright.
2. Write the PR body to a file. Its **first line** must be:

   `**Review comments must go on <SPEC-ISSUE-ID>. Comments on this pull request are never read.**`

   That is not a courtesy — the platform's webhook models only `pull_request` and `ci_status`, so a review left here reaches nobody and the human waits forever believing they replied. Then `Closes <SPEC-ISSUE-ID>` (the spec, not a ticket) so merging completes the spec. Then: what changed, one row per `AC#`/`I#` **that is still live** with the test that covers it, every ticket id with its `Result`, and any `Risks` line from a ticket's report quoted verbatim — the PR body is the only place a human ever sees one. **Leave out every number a `**Spec correction**` retired** and say in one line which were retired and which ticket acted on it: a retired criterion's row would cite a test that has been deleted.
3. **Try the update first, always**: `tools/github-pr.sh --update <owner/repo> <branch> <body-file>`.
   - It prints a URL → a pull request was already open and now carries this body.
   - It prints `none` → no pull request is open. Create one: `tools/github-pr.sh <owner/repo> <branch> main "<title>" <body-file>`, which prints the URL.

   Update-first is the order because the only other record of an open pull request is the URL in your own `**Status**` comment, which you write *after* opening one — so a run that opened one and died leaves no record, and a create would then fail. Rebuild the whole body from the ticket reports every time you update: later commits reach an open pull request by themselves, but its body does not, so a criterion added after it was opened is invisible to the human until you do this.
4. Never merge it. Merging is the human gate.
