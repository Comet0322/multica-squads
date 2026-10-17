#!/usr/bin/env bash
# Open a pull request on the local Forgejo. Usage:
#   forgejo-pr.sh <repo-name> <head-branch> <base-branch> <title> <body-file>
# Reads the token from forgejo/.env (never printed). Prints the PR URL.
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
set -a; . "$DIR/forgejo/.env"; set +a
repo="$1"; head="$2"; base="$3"; title="$4"; body_file="$5"
payload=$(jq -n --arg t "$title" --arg h "$head" --arg b "$base" --rawfile body "$body_file" \
  '{title:$t, head:$h, base:$b, body:$body}')
curl -fsS -X POST "http://127.0.0.1:13000/api/v1/repos/${FORGEJO_ADMIN_USER}/${repo}/pulls" \
  -H "Authorization: token ${FORGEJO_TOKEN}" -H 'Content-Type: application/json' -d "$payload" | jq -r .html_url
