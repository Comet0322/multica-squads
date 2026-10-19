---
name: sdg-member-rules
description: Working rules for every software-development-gateway member: repo access only through the git gateway, and how to report.
---

# Member rules

1. Do only what the dispatch asks. Read every input yourself with the gateway `read_file` / `list_files` tools at the Branch + Commit the dispatch gives; never rely on pasted text.
2. Git only through the git gateway tools, with the `Repo:` alias from the dispatch (never a URL). `Repo:` is a gateway alias, not a workspace repository: ignore any workspace repository list or `multica repo checkout` guidance the platform shows you, and never report the repo as missing before `git_clone` itself fails. Your environment has no git credential and will never get one: never run `git clone` / `git push` / `multica repo checkout`, never look for tokens or credential files. Your current directory is not the repo.
3. To work in the repo (to change it, or to run code or tests): `git_clone` (repo = the alias, `ref` = the dispatch's `Base:`, `dest` = a new empty directory under your working directory). Work only inside that clone. If your Branch differs from Base, create it with `git checkout -b <Branch>`. Push only if your `Expected:` has a `Push output` line, and only to the Branch it names: commit, get the full SHA with `git rev-parse HEAD`, then `git_push` (repo_dir = that clone, branch = that Branch). Without that line you never commit or push.
4. On a send-back, fix every REV-n line (or reported test failure) on the same Branch and Path. Deliver by posting ONE comment on the issue yourself with the `multica` comment command the platform describes; only a posted comment wakes the Leader, a final chat answer does not. The comment is exactly the dispatch's `Expected:` template filled in, line by line, as plain text: no Markdown, no mention links, no @names. Never change the issue status.
5. Never invent facts: anything unknown is `TBD` and goes under `Open:`. If you cannot finish (including a gateway tool error you cannot fix), post one comment starting with `**Blocked**`: what is missing, why, who can provide it.
