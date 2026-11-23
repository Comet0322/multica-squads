---
name: bp-environment
description: Where the repo comes from, where work is pushed, and how the pull request is opened on GitHub
---

# Environment

- The clone URL is in the spec issue. Get a worktree with `multica repo checkout <url>`.
- Work on a feature branch off `origin/main`, never on `main`. The branch name is given in the dev issue; the first agent creates it, later ones `git fetch origin && git checkout -B <branch> origin/<branch>`. Push with `git push -u origin <branch>`; the credential is already set up. `main` is protected.
- Commit as yourself, with `-c user.name=<your agent name> -c user.email=<your agent name>@multica.local`. Never run `git config`: a worktree shares the repository's config.
- Never print a credential, never merge.
- The leader opens the pull request: write the body to a file, then `tools/github-pr.sh --update <owner/repo> <branch> <body-file>`; if it prints `none`, `tools/github-pr.sh <owner/repo> <branch> main "<title>" <body-file>`. The body starts with `Closes <SPEC-ISSUE-ID>` and lists each criterion with its evidence and each gate verdict.
