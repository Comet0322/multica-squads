---
name: multica-platform-git-host
description: Open a pull request / merge request on the code host and read its state (open / merged / closed) - Forgejo/Gitea, GitLab or Azure DevOps. Platform skill; opens and reads only, never merges; the repo address comes from the repo bound in Multica, not from this skill.
metadata:
  credentials:
    priority:
      - GIT_HOST_TOKEN (variable name per token_env in config.yaml)
  runtime:
    python: ">=3.9"
    deps: none
---

# Platform · Git Host

## Purpose

Turn the delivery branch into a PR (a MR on GitLab) and return its link. **Opens only, never merges**: the script has no merge capability; merging is done by a human.

Which repo is decided by the Multica project binding; the script reads the current repo's `git remote get-url origin`, so **never write the repo address here or in prompts**. Host type and token variable name are company-level and live only in `config.yaml`.

## Standard flow

```bash
# 1. Write the PR description to a file (gate verdicts, AC table, known limitations, items for the human)
# 2. Dry-run first to confirm the request targets the right place
python scripts/open_pr.py --head release/<ISSUE-KEY>-<slug> --title "<ISSUE-KEY> <title>" --body-file pr-body.md --dry-run
# 3. Open the PR; prints one JSON line: {"url": "...", "number": N, "existing": false}
python scripts/open_pr.py --head release/<ISSUE-KEY>-<slug> --title "<ISSUE-KEY> <title>" --body-file pr-body.md
```

- If an open PR for the same head exists, it is returned (`existing: true`), not duplicated.
- `--base` defaults to `default_base` in `config.yaml` (`main`).
- A message starting with `BLOCKED:` (type not configured, empty token) goes into the Status comment as-is and is escalated to a human; do not guess.

## Check whether a PR was merged

```bash
# prints one JSON line: {"number": N, "state": "open|merged|closed", "merged": true, "head_sha": "...", "merge_sha": "...", "url": "..."}
python scripts/pr_status.py --number <N>
```

Read-only. Used by the Leader to confirm a human really merged before closing the Issue.

## Files

```text
multica-platform-git-host/
├── SKILL.md
├── config.yaml        # type / token_env / default_base (no credentials)
├── .env.example
├── scripts/open_pr.py   # stdlib only
└── scripts/pr_status.py # read-only PR state
```

## Configuration (filled once by the team)

| Key | Meaning |
| --- | --- |
| `type` | `forgejo` (incl. Gitea) / `gitlab` / `azure` |
| `token_env` | Env var holding the token; the token may only open PRs |
| `default_base` | PR target branch, default `main` |

Endpoints: Forgejo `POST /api/v1/repos/<owner>/<repo>/pulls`; GitLab `POST /api/v4/projects/<path>/merge_requests`; Azure DevOps `POST <org>/<project>/_apis/git/repositories/<repo>/pullrequests`.

## Prohibited

- Never merge, approve or close a PR.
- Never put the token in Git, a PR description or a comment.
- Never guess the host type; if unset, BLOCKED.
