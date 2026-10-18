#!/usr/bin/env bash
# Open a pull request on the local Forgejo, or replace an open one's body. Usage:
#   forgejo-pr.sh <repo-name> <head-branch> <base-branch> <title> <body-file>
#   forgejo-pr.sh --update <repo-name> <head-branch> <body-file>
# A later ticket's commits land on an open PR by themselves, but its body does not:
# --update rewrites the body of the open PR whose head is <head-branch>, which is how
# a criterion added after the PR was opened reaches the one artefact a human reads.
# Reads the token from forgejo/.env (never printed). Prints the PR URL.
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
set -a; . "$DIR/forgejo/.env"; set +a
api="http://127.0.0.1:13000/api/v1/repos"

if [ "${1:-}" = "--update" ]; then
  repo="$2"; head="$3"; body_file="$4"
  num=$(curl -fsS "${api}/${FORGEJO_ADMIN_USER}/${repo}/pulls?state=open" \
    -H "Authorization: token ${FORGEJO_TOKEN}" \
    | jq -r --arg h "$head" 'map(select(.head.ref == $h)) | .[0].number // empty')
  [ -n "$num" ] || { echo "no open PR with head '$head' in ${repo}" >&2; exit 1; }
  curl -fsS -X PATCH "${api}/${FORGEJO_ADMIN_USER}/${repo}/pulls/${num}" \
    -H "Authorization: token ${FORGEJO_TOKEN}" -H 'Content-Type: application/json' \
    -d "$(jq -n --rawfile body "$body_file" '{body:$body}')" | jq -r .html_url
  exit 0
fi

repo="$1"; head="$2"; base="$3"; title="$4"; body_file="$5"
payload=$(jq -n --arg t "$title" --arg h "$head" --arg b "$base" --rawfile body "$body_file" \
  '{title:$t, head:$h, base:$b, body:$body}')
curl -fsS -X POST "${api}/${FORGEJO_ADMIN_USER}/${repo}/pulls" \
  -H "Authorization: token ${FORGEJO_TOKEN}" -H 'Content-Type: application/json' -d "$payload" | jq -r .html_url
