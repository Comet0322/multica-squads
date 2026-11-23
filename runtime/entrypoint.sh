#!/usr/bin/env bash
# The daemon authenticates from ~/.multica/config.json only (not MULTICA_TOKEN), so
# materialise it from the environment at start. The token never lands in the image.
set -euo pipefail
: "${MULTICA_TOKEN:?MULTICA_TOKEN is not set (see runtime/.env)}"
: "${MULTICA_SERVER_URL:?MULTICA_SERVER_URL is not set}"
umask 077
mkdir -p "$HOME/.multica"
jq -n --arg s "$MULTICA_SERVER_URL" --arg t "$MULTICA_TOKEN" \
  '{server_url:$s, app_url:($ENV.MULTICA_APP_URL // "http://localhost:13654"), token:$t}' > "$HOME/.multica/config.json"
exec "$@"
