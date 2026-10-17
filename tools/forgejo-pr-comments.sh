#!/usr/bin/env bash
# List the comments, reviews and review line-comments on a Forgejo pull request
# as one JSON array, oldest first. Usage:
#   forgejo-pr-comments.sh <repo-name> <pr-number>
# Reads the token from forgejo/.env (never printed).
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
set -a; . "$DIR/forgejo/.env"; set +a
repo="$1"; num="$2"
api="http://127.0.0.1:13000/api/v1/repos/${FORGEJO_ADMIN_USER}/${repo}"
get() { curl -fsS -H "Authorization: token ${FORGEJO_TOKEN}" "$1"; }

comments=$(get "${api}/issues/${num}/comments")
reviews=$(get "${api}/pulls/${num}/reviews")
line_comments='[]'
for id in $(jq -r '.[]?.id' <<<"$reviews"); do
  rc=$(get "${api}/pulls/${num}/reviews/${id}/comments")
  line_comments=$(jq -n --argjson a "$line_comments" --argjson b "$rc" '$a + $b')
done

jq -n --argjson c "$comments" --argjson r "$reviews" --argjson l "$line_comments" '
  [ ($c[]? | {kind:"comment",      author:.user.login, created:.created_at,   body:.body}),
    ($r[]? | select((.body // "") != "")
           | {kind:"review",       author:.user.login, created:.submitted_at, state:.state, body:.body}),
    ($l[]? | {kind:"review-line",  author:.user.login, created:.created_at,   path:.path, line:.original_line, body:.body}) ]
  | map(select((.body // "") != "")) | sort_by(.created)'
