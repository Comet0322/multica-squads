#!/usr/bin/env bash
# List the comments, reviews and review line-comments on a GitHub pull request
# as one JSON array, oldest first. Usage:
#   github-pr-comments.sh <repo> <pr-number>      (<repo> is `owner/name` or `name`)
# Authenticates through `gh` (nothing is printed).
set -euo pipefail
repo="$1"; num="$2"
case "$repo" in */*) ;; *) repo="$(gh api user -q .login)/$repo";; esac
api="repos/${repo}"

comments=$(gh api --paginate "${api}/issues/${num}/comments" | jq -s 'add // []')
reviews=$(gh api --paginate "${api}/pulls/${num}/reviews" | jq -s 'add // []')
line_comments=$(gh api --paginate "${api}/pulls/${num}/comments" | jq -s 'add // []')

jq -n --argjson c "$comments" --argjson r "$reviews" --argjson l "$line_comments" '
  [ ($c[]? | {kind:"comment",      author:.user.login, created:.created_at,   body:.body}),
    ($r[]? | select((.body // "") != "")
           | {kind:"review",       author:.user.login, created:.submitted_at, state:.state, body:.body}),
    ($l[]? | {kind:"review-line",  author:.user.login, created:.created_at,   path:.path, line:(.original_line // .line), body:.body}) ]
  | map(select((.body // "") != "")) | sort_by(.created)'
