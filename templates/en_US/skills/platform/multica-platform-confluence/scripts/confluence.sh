#!/bin/bash
# ============================================
# Confluence API wrapper (v2.2 - config-driven + legacy username/password auth)
# Reads credentials from .env and config from config.yaml
# ============================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Load .env and resolve credentials (domain account first)
# shellcheck disable=SC1091
source "$SCRIPT_DIR/credentials.sh"
load_skill_env "$SKILL_DIR"
resolve_credentials

# Load config.yaml (parsed with python, because handling YAML in bash is painful)
parse_config() {
  local key="$1"
  python3 -c "
import yaml, sys
try:
    with open('$SKILL_DIR/config.yaml') as f:
        config = yaml.safe_load(f)
    keys = '$key'.split('.')
    val = config
    for k in keys:
        val = val[k]
    print(val)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null || echo ""
}

# Get credentials
CONFLUENCE_URL="${CONFLUENCE_URL:-$(parse_config confluence.url 2>/dev/null || echo 'http://your-domain.atlassian.net/wiki:8090')}"
CONFLUENCE_TOKEN="${CONFLUENCE_TOKEN:-${CONFLUENCE_PAT:-}}"
CONFLUENCE_AUTH_MODE="${CONFLUENCE_AUTH_MODE:-basic}"  # basic | form | token
DEFAULT_SPACE="${DEFAULT_SPACE:-$(parse_config confluence.default_space 2>/dev/null || echo 'TEAM')}"
DEFAULT_PARENT="${DEFAULT_PARENT:-$(parse_config confluence.default_parent_page_id 2>/dev/null || echo '234567')}"

# Check credentials
CURL_AUTH_ARGS=()
COOKIE_JAR=""

cleanup_auth() {
  if [ -n "$COOKIE_JAR" ] && [ -f "$COOKIE_JAR" ]; then
    rm -f "$COOKIE_JAR"
  fi
}
trap cleanup_auth EXIT

require_user_pass() {
  if [ -z "$CONFLUENCE_USER" ] || [ -z "$CONFLUENCE_PASS" ]; then
    echo "❌ Credentials not configured. Set JIRA_USERNAME / JIRA_PASSWORD, or set CONFLUENCE_USER and CONFLUENCE_PASS in .env"
    exit 1
  fi
}

form_login() {
  require_user_pass
  COOKIE_JAR="$(mktemp "${TMPDIR:-/tmp}/confluence-cookie.XXXXXX")"

  local login_resp http_code
  login_resp=$(curl -s -w "\n%{http_code}" \
    -c "$COOKIE_JAR" \
    -X POST "$CONFLUENCE_URL/dologin.action" \
    --data-urlencode "os_username=$CONFLUENCE_USER" \
    --data-urlencode "os_password=$CONFLUENCE_PASS" \
    --data "os_cookie=true" \
    --data "os_destination=/rest/api/user/current" \
    --data "login=Log in")
  http_code=$(echo "$login_resp" | tail -1)

  if [ "$http_code" != "200" ] && [ "$http_code" != "302" ]; then
    echo "❌ Confluence form login failed (HTTP $http_code)"
    exit 1
  fi

  CURL_AUTH_ARGS=(-b "$COOKIE_JAR")
}

check_auth() {
  CURL_AUTH_ARGS=()

  case "$CONFLUENCE_AUTH_MODE" in
    basic)
      require_user_pass
      CURL_AUTH_ARGS=(--basic -u "$CONFLUENCE_USER:$CONFLUENCE_PASS")
      ;;
    form)
      form_login
      ;;
    token)
      if [ -z "$CONFLUENCE_TOKEN" ]; then
        echo "❌ CONFLUENCE_AUTH_MODE=token but CONFLUENCE_TOKEN / CONFLUENCE_PAT is not configured"
        exit 1
      fi
      CURL_AUTH_ARGS=(-H "Authorization: Bearer $CONFLUENCE_TOKEN")
      ;;
    *)
      echo "❌ Unknown CONFLUENCE_AUTH_MODE: $CONFLUENCE_AUTH_MODE"
      echo "   Allowed values: basic, form, token"
      exit 1
      ;;
  esac
}

print_auth_hint() {
  local body="$1"
  if echo "$body" | grep -qiE 'AUTHENTICATION_DENIED|oauth|WWW-Authenticate'; then
    echo ""
    echo "Authentication hint: Confluence rejected the current user's credentials."
    echo "By default this skill uses legacy Confluence username/password Basic Auth."
    echo "If you can log in from a browser but REST Basic fails, try CONFLUENCE_AUTH_MODE=form, or check whether the server has disabled REST Basic."
  fi
}

# ── Command implementations ──────────────────────────────

create_page() {
  local title="${1:-}"
  local parent_id="${2:-$DEFAULT_PARENT}"
  local content="${3:-<p>Empty page</p>}"
  local space="${4:-$DEFAULT_SPACE}"

  if [ -z "$title" ] || [ -z "$parent_id" ]; then
    echo "Usage: $0 create-page <title> [parent_id] [content] [space_key]"
    echo ""
    echo "Current defaults:"
    echo "  Space: $DEFAULT_SPACE"
    echo "  Parent page ID: $DEFAULT_PARENT"
    exit 1
  fi

  check_auth

  local resp
  local payload
  payload=$(TITLE="$title" PARENT_ID="$parent_id" CONTENT="$content" SPACE="$space" python3 - <<'PY'
import json
import os

print(json.dumps({
    "type": "page",
    "title": os.environ["TITLE"],
    "ancestors": [{"id": os.environ["PARENT_ID"]}],
    "space": {"key": os.environ["SPACE"]},
    "body": {
        "storage": {
            "value": os.environ["CONTENT"],
            "representation": "storage",
        }
    },
}, ensure_ascii=False))
PY
)

  resp=$(curl -s -w "\n%{http_code}" "${CURL_AUTH_ARGS[@]}" \
    -X POST "$CONFLUENCE_URL/rest/api/content/" \
    -H "Content-Type: application/json" \
    -d "$payload")

  local http_code
  http_code=$(echo "$resp" | tail -1)
  local body
  body=$(echo "$resp" | sed '$d')

  if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
    local page_id title_out
    page_id=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "unknown")
    title_out=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])" 2>/dev/null || echo "$title")
    echo "✅ Confluence page created"
    echo "  Title: $title_out"
    echo "  ID: $page_id"
    echo "  Link: $CONFLUENCE_URL/pages/viewpage.action?pageId=$page_id"
  else
    echo "❌ Creation failed (HTTP $http_code)"
    echo "$body"
    print_auth_hint "$body"
    exit 1
  fi
}

fetch_page() {
  local page_id="${1:-}"
  local output_dir="${2:-}"
  local jira_key="${3:-}"

  if [ -z "$page_id" ]; then
    echo "Usage: $0 fetch-page <page_id> [output_dir] [jira_key]"
    exit 1
  fi
  check_auth

  local args=(python3 "$SCRIPT_DIR/fetch_page.py" "$page_id")
  [ -n "$output_dir" ] && args+=(--output-dir "$output_dir")
  [ -n "$jira_key" ] && args+=(--jira-key "$jira_key")
  "${args[@]}"
}

get_page() {
  local page_id="${1:-}"

  if [ -z "$page_id" ]; then
    echo "Usage: $0 get-page <page_id>"
    exit 1
  fi
  check_auth

  curl -s "${CURL_AUTH_ARGS[@]}" \
    "$CONFLUENCE_URL/rest/api/content/$page_id?expand=body.storage" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"Title: {d.get('title', 'N/A')}\")
print(f\"ID: {d.get('id', 'N/A')}\")
print(f\"Version: {d.get('version', {}).get('number', 'N/A')}\")
print()
body = d.get('body', {}).get('storage', {}).get('value', '')
print(body)
"
}

list_pages() {
  local space="${1:-$DEFAULT_SPACE}"
  check_auth

  curl -s "${CURL_AUTH_ARGS[@]}" \
    "$CONFLUENCE_URL/rest/api/content?spaceKey=$space&type=page&limit=200" \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('results', []):
    print(f\"{r['id']:>12}  {r['title']}\")
"
}

find_page() {
  local title="${1:-}"
  local space="${2:-$DEFAULT_SPACE}"

  if [ -z "$title" ]; then
    echo "Usage: $0 find-page <title> [space_key]"
    exit 1
  fi
  check_auth

  curl -s "${CURL_AUTH_ARGS[@]}" \
    "$CONFLUENCE_URL/rest/api/content?spaceKey=$space&type=page&limit=200" \
    | KEYWORD="$title" python3 -c "
import os
import sys, json
data = json.load(sys.stdin)
keyword = os.environ['KEYWORD'].lower()
for r in data.get('results', []):
    if keyword in r.get('title', '').lower():
        print(f\"{r['id']:>12}  {r['title']}\")
"
}

update_page() {
  local page_id="${1:-}"
  local content="${2:-}"

  if [ -z "$page_id" ] || [ -z "$content" ]; then
    echo "Usage: $0 update-page <page_id> <content>"
    exit 1
  fi
  check_auth

  # Get the current version number first
  local page_json current_version current_title
  page_json=$(curl -s "${CURL_AUTH_ARGS[@]}" \
    "$CONFLUENCE_URL/rest/api/content/$page_id")
  current_version=$(echo "$page_json" | python3 -c "import sys,json; print(json.load(sys.stdin)['version']['number'])")
  current_title=$(echo "$page_json" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")

  local new_version=$((current_version + 1))
  local payload
  payload=$(PAGE_ID="$page_id" TITLE="$current_title" VERSION="$new_version" CONTENT="$content" python3 - <<'PY'
import json
import os

print(json.dumps({
    "id": os.environ["PAGE_ID"],
    "type": "page",
    "title": os.environ["TITLE"],
    "version": {"number": int(os.environ["VERSION"])},
    "body": {
        "storage": {
            "value": os.environ["CONTENT"],
            "representation": "storage",
        }
    },
}, ensure_ascii=False))
PY
)

  curl -s "${CURL_AUTH_ARGS[@]}" \
    -X PUT "$CONFLUENCE_URL/rest/api/content/$page_id" \
    -H "Content-Type: application/json" \
    -d "$payload" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"✅ Page updated to version {d['version']['number']}\")"
}

list_spaces() {
  check_auth
  curl -s "${CURL_AUTH_ARGS[@]}" \
    "$CONFLUENCE_URL/rest/api/space" \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('results', []):
    print(f\"{r['key']:>20}  {r['name']}\")
"
}

# ── Help ──────────────────────────────────

show_help() {
  cat << 'HELP'
Confluence API Wrapper v2.2

Usage: confluence.sh <command> [arguments]

Commands:
  create-page <title> [parent_page_id] [content] [Space]    Create a new page
  fetch-page <page_id> [output_dir] [JIRA_KEY]       Fetch a page as Markdown
  get-page <page_id>                                Get page content
  update-page <page_id> <content>                      Update a page
  list-pages [Space]                                List all pages in a space
  find-page <title> [Space]                         Search pages by title
  list-spaces                                       List all spaces
  help                                              Show this help

Examples:
  confluence.sh create-page "Product Requirements - XXX" 234567 "<h1>Requirements</h1>" TEAM
  confluence.sh get-page 123456
  confluence.sh find-page "Overview Dashboard"
  confluence.sh list-pages TEAM

Configuration:
  Credentials are set via .env or environment variables (domain account first):
    JIRA_USERNAME, JIRA_PASSWORD
    CONFLUENCE_URL, CONFLUENCE_USER, CONFLUENCE_PASS
    CONFLUENCE_AUTH_MODE=basic   default; legacy Confluence username/password Basic Auth
    CONFLUENCE_AUTH_MODE=form    legacy form-login cookie mode
    CONFLUENCE_AUTH_MODE=token   optional Bearer Token mode
  Project configuration is in config.yaml:
    confluence.default_space, confluence.default_parent_page_id
HELP
}

# ── Main entry ────────────────────────────────

case "${1:-help}" in
  create-page)    create_page "${2:-}" "${3:-}" "${4:-}" "${5:-}" ;;
  fetch-page)     fetch_page "${2:-}" "${3:-}" "${4:-}" ;;
  get-page)       get_page "${2:-}" ;;
  update-page)    update_page "${2:-}" "${3:-}" ;;
  list-pages)     list_pages "${2:-$DEFAULT_SPACE}" ;;
  find-page)      find_page "${2:-}" "${3:-}" ;;
  list-spaces)    list_spaces ;;
  help|--help|-h) show_help ;;
  *)
    echo "Unknown command: ${1:-}"
    echo "Run '$0 help' for usage"
    exit 1
    ;;
esac
