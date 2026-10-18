#!/bin/bash
# ============================================
# JIRA API wrapper (v2.0 - config-driven)
# Reads credentials from .env and project config from config.yaml
# ============================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$SKILL_DIR/config.yaml"

# ── Config loading ──────────────────────────────

# Load .env and resolve credentials (domain account first)
# shellcheck disable=SC1091
source "$SCRIPT_DIR/credentials.sh"
load_skill_env "$SKILL_DIR"
resolve_credentials

# Parse the YAML config with Python
yaml_get() {
  python3 -c "
import yaml, sys
try:
    with open('$CONFIG_FILE') as f:
        config = yaml.safe_load(f)
    keys = '$1'.split('.')
    val = config
    for k in keys:
        if isinstance(val, dict):
            val = val[k]
        elif isinstance(val, list):
            val = val[int(k)]
        else:
            print(f'ERROR: cannot index into {type(val)}', file=sys.stderr)
            sys.exit(1)
    if isinstance(val, (dict, list)):
        print(yaml.dump(val, default_flow_style=False))
    else:
        print(val)
except Exception as e:
    print(f'CONFIG_ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null
}

yaml_get_optional() {
  yaml_get "$1" 2>/dev/null | tr -d '\n' || true
}

JIRA_URL="${JIRA_URL:-$(yaml_get_optional jira.url)}"
JIRA_URL="${JIRA_URL:-http://your-domain.atlassian.net:8080}"
CONFLUENCE_URL="${CONFLUENCE_URL:-$(yaml_get_optional confluence.url)}"
CONFLUENCE_URL="${CONFLUENCE_URL:-http://your-domain.atlassian.net/wiki:8090}"

# Get the project field mapping from config.yaml
get_project_field() {
  local project="$1"
  local field="$2"
  yaml_get "projects.$project.fields.$field.customId" | tr -d '\n'
}

field_key() {
  local project="$1"
  local field="$2"
  local custom_id
  custom_id=$(get_project_field "$project" "$field")
  printf 'customfield_%s' "$custom_id"
}

field_key_or_default() {
  local project="$1"
  local field="$2"
  local fallback="$3"
  local custom_id
  custom_id=$(yaml_get_optional "projects.$project.fields.$field.customId")
  if [ -n "$custom_id" ]; then
    printf 'customfield_%s' "$custom_id"
  else
    printf '%s' "$fallback"
  fi
}

workflow_field_key() {
  local project="$1"
  local field="$2"
  local fallback="$3"
  local custom_id
  custom_id=$(yaml_get_optional "projects.$project.workflow_fields.$field.customId")
  if [ -z "$custom_id" ]; then
    custom_id=$(yaml_get_optional "workflow_fields.$field.customId")
  fi
  custom_id="${custom_id:-$fallback}"
  printf 'customfield_%s' "$custom_id"
}

get_issue_project() {
  local issue_key="$1"
  printf '%s' "${issue_key%%-*}"
}

get_jira_issue_type_id() {
  local issue_type_id
  issue_type_id=$(yaml_get_optional jira.issue_type_id)
  printf '%s' "${issue_type_id:-10001}"
}

get_project_id() {
  local project="$1"
  yaml_get "projects.$project.id" | tr -d '\n'
}

get_project_default_epic() {
  local project="$1"
  yaml_get "projects.$project.default_epic" | tr -d '\n'
}

get_default() {
  yaml_get "defaults.$1" | tr -d '\n'
}

# Get the field option ID
get_field_option_id() {
  local project="$1"
  local field="$2"
  local label="$3"
  python3 -c "
import yaml
with open('$CONFIG_FILE') as f:
    config = yaml.safe_load(f)
options = config['projects']['$project']['field_options']['$field']
for o in options:
    if o['label'] == '$label':
        print(o['id'])
        break
" 2>/dev/null
}

# ── Credential check ──────────────────────────────

check_auth() {
  if [ -z "$JIRA_USER" ] || [ -z "$JIRA_PASS" ]; then
    echo "❌ Credentials not configured. Set JIRA_USERNAME / JIRA_PASSWORD, or set JIRA_USER and JIRA_PASS in .env"
    exit 1
  fi
}

# ── Weekly report records (OBSIDIAN integration) ──────────────

OBSIDIAN_ROOT="${OBSIDIAN_ROOT:-}"
JIRA_NOTIFY_RECORD_DIR="${JIRA_NOTIFY_RECORD_DIR:-${OBSIDIAN_ROOT:+$OBSIDIAN_ROOT/06-inbox/jira-notify-records}}"
BASE_SERVICE_WEEKLY_DIR="${BASE_SERVICE_WEEKLY_DIR:-${OBSIDIAN_ROOT:+$OBSIDIAN_ROOT/06-inbox/base-service-weekly-materials}}"
ROLLUP_CONFIG_PATH="${ROLLUP_CONFIG_PATH:-${OBSIDIAN_ROOT:+$OBSIDIAN_ROOT/tools/dingtalk_progress_bot/config.local.json}}"
ROLLUP_MAIN_PY="${ROLLUP_MAIN_PY:-${OBSIDIAN_ROOT:+$OBSIDIAN_ROOT/tools/dingtalk_progress_bot/main.py}}"

ensure_dirs() {
  if [ -z "$JIRA_NOTIFY_RECORD_DIR" ] || [ -z "$BASE_SERVICE_WEEKLY_DIR" ]; then
    return 1
  fi
  mkdir -p "$JIRA_NOTIFY_RECORD_DIR" "$BASE_SERVICE_WEEKLY_DIR"
}

sanitize_filename() {
  echo "$1" | tr '[:space:]' '-' | tr -cd '[:alnum:]-_' | cut -c1-40
}

record_notify_for_weekly() {
  local title="$1"
  local content="$2"
  local webhook_token="$3"
  local project_type="$4"
  local send_result="$5"

  if ! ensure_dirs; then
    return 0
  fi

  local now_date now_time unix_ts rand suffix msg_id short_title short_text
  now_date="$(date +%Y%m%d)"
  now_time="$(date '+%Y-%m-%d %H:%M:%S')"
  unix_ts="$(date +%s)"
  rand="$RANDOM"
  short_title="$(sanitize_filename "$title")"
  short_text="$(echo "$content" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g' | cut -c1-200)"
  suffix="${now_date}-${short_title}-${unix_ts}-${rand}"
  msg_id="jira-notify-${unix_ts}-${rand}"

  local record_json="$JIRA_NOTIFY_RECORD_DIR/${suffix}.notify.json"
  local record_md="$JIRA_NOTIFY_RECORD_DIR/${suffix}.notify.md"
  local weekly_json="$BASE_SERVICE_WEEKLY_DIR/${now_date}-${short_title}-${msg_id}.weekly.json"
  local weekly_md="$BASE_SERVICE_WEEKLY_DIR/${now_date}-${short_title}-${msg_id}.weekly.md"

  cat > "$record_json" << EOF
{
  "msg_id": "$msg_id",
  "received_at": "$now_time",
  "sender": "jira.sh",
  "sender_staff_id": "$JIRA_USER",
  "conversation_id": "dingtalk-webhook:$project_type",
  "conversation_title": "JIRA-auto-notify-$project_type",
  "conversation_type": "webhook",
  "receive_mode": "direct-from-script",
  "message_type": "markdown",
  "text": "$short_text",
  "title": "$title",
  "project_type": "$project_type",
  "webhook_token_masked": "${webhook_token:0:6}***${webhook_token: -6}",
  "reason": "jira.sh notify-dingtalk auto-record",
  "send_result": $send_result
}
EOF

  cat > "$record_md" << EOF
# JIRA Notification Send Record

- Time: $now_time
- Source: jira.sh / notify-dingtalk
- Project type: $project_type
- Title: $title
- Content summary: $short_text

## Send result

\`\`\`json
$send_result
\`\`\`
EOF

  cat > "$weekly_json" << EOF
{
  "msg_id": "$msg_id",
  "received_at": "$now_time",
  "sender": "jira.sh",
  "conversation_title": "JIRA-auto-notify-$project_type",
  "receive_mode": "direct-from-script",
  "text": "[$title] $short_text",
  "reason": "jira.sh notify-dingtalk auto-record",
  "weekly_sync_reason": "auto-added to weekly report materials after jira.sh sent a DingTalk notification successfully"
}
EOF

  cat > "$weekly_md" << EOF
# Personal Assistant Base Services Team Weekly Report Material Record

- Received at: $now_time
- Channel: JIRA auto-notification
- Conversation title: JIRA-auto-notify-$project_type
- Conversation type: webhook
- Receive mode: direct-from-script
- Sender: jira.sh
- Message type: markdown
- Record track: base-service-weekly-materials
- Classification: work item
- Record section: work item
- Basis: auto-added to weekly report materials after jira.sh sent a DingTalk notification successfully
- Sync to base services team weekly materials: yes
- Weekly sync basis: auto-added to weekly report materials after jira.sh sent a DingTalk notification successfully

## Weekly report material text

[$title] $short_text
EOF

  if [ -n "$ROLLUP_MAIN_PY" ] && [ -n "$ROLLUP_CONFIG_PATH" ] && [ -f "$ROLLUP_MAIN_PY" ] && [ -f "$ROLLUP_CONFIG_PATH" ]; then
    python3 "$ROLLUP_MAIN_PY" --config "$ROLLUP_CONFIG_PATH" --rebuild-rollups >/dev/null 2>&1 || true
  fi
}

# ── Command implementations ──────────────────────────────

# Create a Story (generic; --project selects the project)
create_story() {
  local project="" summary="" description="" epic_link=""
  local need_user="" background=""
  local center_source="" region_source="" req_type="" compliance=""

  # Parse arguments
  while [ $# -gt 0 ]; do
    case "$1" in
      --project)       project="$2"; shift 2 ;;
      --summary)       summary="$2"; shift 2 ;;
      --description)   description="$2"; shift 2 ;;
      --epic)          epic_link="$2"; shift 2 ;;
      --need-user)     need_user="$2"; shift 2 ;;
      --background)    background="$2"; shift 2 ;;
      --center-source) center_source="$2"; shift 2 ;;
      --region-source) region_source="$2"; shift 2 ;;
      --req-type)      req_type="$2"; shift 2 ;;
      --compliance)    compliance="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [ -z "$project" ] || [ -z "$summary" ]; then
    echo "Usage: $0 create-story --project <PROJ|PLAT> --summary \"Title\" [other options]"
    echo ""
    echo "Required:"
    echo "  --project       Project code (PROJ or PLAT)"
    echo "  --summary       Story title"
    echo ""
    echo "Optional (config.yaml defaults are used when omitted):"
    echo "  --description   Description text"
    echo "  --epic          Epic Link Key"
    echo "  --need-user     Requester username"
    echo "  --background    Background"
    echo "  --center-source Requirement source (center level)"
    echo "  --region-source Requirement source (region)"
    echo "  --req-type      Requirement type"
    echo "  --compliance    Compliance involved"
    exit 1
  fi

  check_auth

  # Apply defaults
  local project_id epic_key issue_type_id
  project_id=$(yaml_get_optional "projects.$project.id")
  issue_type_id=$(get_jira_issue_type_id)
  epic_key="${epic_link:-$(yaml_get_optional "projects.$project.default_epic")}"
  need_user="${need_user:-$(get_default need_user)}"
  background="${background:-$(get_default background)}"
  center_source="${center_source:-$(get_default center_source)}"
  region_source="${region_source:-$(get_default region_source)}"
  req_type="${req_type:-$(get_default req_type)}"
  compliance="${compliance:-$(get_default compliance)}"

  if [ -z "$project_id" ]; then
    echo "❌ Unknown project: $project"
    echo "   Available projects: $(yaml_get projects | grep -E '^  [A-Z]+:' | sed 's/:$//' | tr '\n' ' ')"
    exit 1
  fi

  # Look up option IDs
  local center_id region_id type_id compliance_id
  center_id=$(get_field_option_id "$project" center_source "$center_source")
  region_id=$(get_field_option_id "$project" region_source "$region_source")
  type_id=$(get_field_option_id "$project" req_type "$req_type")
  compliance_id=$(get_field_option_id "$project" compliance "$compliance")

  if [ -z "$center_id" ] || [ -z "$region_id" ] || [ -z "$type_id" ] || [ -z "$compliance_id" ]; then
    echo "❌ Field option not matched; check field_options in config.yaml"
    echo "  center_source=$center_source -> $center_id"
    echo "  region_source=$region_source -> $region_id"
    echo "  req_type=$req_type -> $type_id"
    echo "  compliance=$compliance -> $compliance_id"
    exit 1
  fi

  echo "📋 About to create JIRA Story:"
  echo "  Project: $project (ID: $project_id)"
  echo "  Issue Type: $issue_type_id"
  echo "  Title: $summary"
  echo "  Epic: $epic_key"
  echo "  Requester: $need_user"
  echo "  Center source: $center_source (ID: $center_id)"
  echo "  Region source: $region_source (ID: $region_id)"
  echo "  Requirement type: $req_type (ID: $type_id)"
  echo "  Compliance: $compliance (ID: $compliance_id)"
  echo ""

  # Build the payload
  local payload need_user_field background_field center_source_field region_source_field req_type_field compliance_field epic_field
  need_user_field=$(field_key "$project" need_user)
  background_field=$(field_key "$project" background)
  center_source_field=$(field_key "$project" center_source)
  region_source_field=$(field_key "$project" region_source)
  req_type_field=$(field_key "$project" req_type)
  compliance_field=$(field_key "$project" compliance)
  epic_field=$(field_key "$project" epic_link)

  payload=$(PROJECT_ID="$project_id" \
    ISSUE_TYPE_ID="$issue_type_id" \
    SUMMARY="$summary" \
    DESCRIPTION="${description:-}" \
    NEED_USER="$need_user" \
    BACKGROUND="$background" \
    CENTER_ID="$center_id" \
    REGION_ID="$region_id" \
    TYPE_ID="$type_id" \
    COMPLIANCE_ID="$compliance_id" \
    EPIC_KEY="$epic_key" \
    NEED_USER_FIELD="$need_user_field" \
    BACKGROUND_FIELD="$background_field" \
    CENTER_SOURCE_FIELD="$center_source_field" \
    REGION_SOURCE_FIELD="$region_source_field" \
    REQ_TYPE_FIELD="$req_type_field" \
    COMPLIANCE_FIELD="$compliance_field" \
    EPIC_FIELD="$epic_field" \
    python3 - <<'PY'
import json
import os

payload = {
    'fields': {
        'project': {'id': os.environ['PROJECT_ID']},
        'issuetype': {'id': os.environ['ISSUE_TYPE_ID']},
        'summary': os.environ['SUMMARY'],
        'description': os.environ.get('DESCRIPTION', ''),
        os.environ['NEED_USER_FIELD']: {'name': os.environ['NEED_USER']},
        os.environ['BACKGROUND_FIELD']: os.environ['BACKGROUND'],
        os.environ['CENTER_SOURCE_FIELD']: [{'id': os.environ['CENTER_ID']}],
        os.environ['REGION_SOURCE_FIELD']: {'id': os.environ['REGION_ID']},
        os.environ['REQ_TYPE_FIELD']: [{'id': os.environ['TYPE_ID']}],
        os.environ['COMPLIANCE_FIELD']: {'id': os.environ['COMPLIANCE_ID']},
        os.environ['EPIC_FIELD']: os.environ['EPIC_KEY'],
    }
}
print(json.dumps(payload, ensure_ascii=False))
PY
)

  # Send the request
  local resp http_code
  resp=$(curl -s -w "\n%{http_code}" -u "$JIRA_USER:$JIRA_PASS" \
    -X POST "$JIRA_URL/rest/api/2/issue/" \
    -H "Content-Type: application/json" \
    -d "$payload")

  http_code=$(echo "$resp" | tail -1)
  local body
  body=$(echo "$resp" | sed '$d')

  if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
    local issue_key
    issue_key=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin)['key'])" 2>/dev/null)
    echo "✅ JIRA Story created: $issue_key"
    echo "   Link: $JIRA_URL/browse/$issue_key"
    echo "$issue_key"  # Output the key for later use
  else
    echo "❌ Creation failed (HTTP $http_code)"
    echo "$body" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if 'errors' in d:
        for k, v in d['errors'].items():
            print(f'  {k}: {v}')
except: print(sys.stdin.read())
" 2>/dev/null || echo "$body"
    exit 1
  fi
}

# Get an Issue
get_issue() {
  local key="$1"
  if [ -z "$key" ]; then echo "Usage: $0 get-issue <ISSUE_KEY>"; exit 1; fi
  check_auth

  curl -s -u "$JIRA_USER:$JIRA_PASS" "$JIRA_URL/rest/api/2/issue/$key" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
f = d.get('fields', {})
print(f\"Key:     {d['key']}\")
print(f\"Title:    {f.get('summary', 'N/A')}\")
print(f\"Status:   {f.get('status', {}).get('name', 'N/A')}\")
print(f\"Type:     {f.get('issuetype', {}).get('name', 'N/A')}\")
print(f\"Project:  {f.get('project', {}).get('name', 'N/A')}\")
assignee = f.get('assignee')
print(f\"Assignee: {assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'}\")
print()
print(f.get('description', 'No description'))
"
}

# Parse the Confluence page URL or pageId from the Issue description / remote links
get_confluence_url() {
  local key="$1"
  local format="${2:-text}"  # text | json
  if [ -z "$key" ]; then
    echo "Usage: $0 get-confluence-url <ISSUE_KEY> [text|json]"
    exit 1
  fi
  check_auth
  export JIRA_URL JIRA_USER JIRA_PASS

  ISSUE_KEY="$key" OUTPUT_FORMAT="$format" python3 <<'PY'
import json, os, re, sys, urllib.request, base64

key = os.environ["ISSUE_KEY"]
fmt = os.environ.get("OUTPUT_FORMAT", "text")
base = os.environ["JIRA_URL"].rstrip("/")
auth = base64.b64encode(f"{os.environ['JIRA_USER']}:{os.environ['JIRA_PASS']}".encode()).decode()
headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

def fetch(path):
    req = urllib.request.Request(f"{base}{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)

issue = fetch(f"/rest/api/2/issue/{key}?fields=description")
desc = (issue.get("fields") or {}).get("description") or ""

urls = re.findall(r"https?://[^\s\]|]+confluence[^\s\]|>]+", desc, re.I)
urls += re.findall(r"https?://[^\s\]|]+/pages/viewpage\.action\?pageId=\d+", desc, re.I)
page_ids = re.findall(r"pageId=(\d+)", desc, re.I)

try:
    links = fetch(f"/rest/api/2/issue/{key}/remotelink")
    for item in links:
        url = (item.get("object") or {}).get("url") or ""
        if "confluence" in url.lower() or "pageId=" in url:
            urls.append(url)
            m = re.search(r"pageId=(\d+)", url)
            if m:
                page_ids.append(m.group(1))
except Exception:
    pass

urls = list(dict.fromkeys(urls))
page_ids = list(dict.fromkeys(page_ids))
result = {"issue_key": key, "urls": urls, "page_ids": page_ids}

if fmt == "json":
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    if not urls and not page_ids:
        print(f"No Confluence link found in {key}")
        sys.exit(1)
    for u in urls:
        print(u)
    for pid in page_ids:
        if not any(pid in u for u in urls):
            print(f"pageId={pid}")
PY
}

# Append Wiki-format content to the Issue description (used to write back design document links, etc.)
append_description() {
  local key="$1"
  local wiki_block="$2"
  if [ -z "$key" ] || [ -z "$wiki_block" ]; then
    echo "Usage: $0 append-description <ISSUE_KEY> '<wiki_block>'"
    echo "Example: $0 append-description PROJ-1813 \$'h3. Design Document\\n* [Design|http://...]'"
    exit 1
  fi
  check_auth
  export JIRA_URL JIRA_USER JIRA_PASS

  ISSUE_KEY="$key" WIKI_BLOCK="$wiki_block" python3 <<'PY'
import json, os, sys, urllib.request, base64

key = os.environ["ISSUE_KEY"]
wiki = os.environ["WIKI_BLOCK"]
url_base = os.environ.get("JIRA_URL", "")
user = os.environ.get("JIRA_USER", "")
password = os.environ.get("JIRA_PASS", "")
if not url_base or not user or not password:
    print("ERROR: missing JIRA_URL / credentials", file=sys.stderr)
    sys.exit(2)

auth = base64.b64encode(f"{user}:{password}".encode()).decode()
headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

req = urllib.request.Request(
    f"{url_base.rstrip('/')}/rest/api/2/issue/{key}?fields=description",
    headers=headers,
)
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.load(resp)
desc = data.get("fields", {}).get("description") or ""
new_desc = desc + wiki
payload = json.dumps({"fields": {"description": new_desc}}).encode()
put_req = urllib.request.Request(
    f"{url_base.rstrip('/')}/rest/api/2/issue/{key}",
    data=payload,
    headers={**headers, "Content-Type": "application/json"},
    method="PUT",
)
with urllib.request.urlopen(put_req, timeout=30) as resp:
    resp.read()
print(f"OK appended description to {key}")
PY
}

# JQL search
search_issues() {
  local jql="$1"
  local max="${2:-20}"
  if [ -z "$jql" ]; then echo "Usage: $0 search <JQL> [max_results]"; exit 1; fi
  check_auth

  curl -s -u "$JIRA_USER:$JIRA_PASS" \
    "$JIRA_URL/rest/api/2/search?jql=$(echo "$jql" | python3 -c "import sys,urllib.parse; print(urllib.parse.quote(sys.stdin.read()))")&maxResults=$max" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
for issue in d.get('issues', []):
    f = issue['fields']
    print(f\"{issue['key']:>12}  [{f.get('status',{}).get('name','?'):>6}]  {f.get('summary','')}\")
print(f\"\n{d.get('total', 0)} results\")
"
}

# View editable fields
get_fields() {
  local key="$1"
  if [ -z "$key" ]; then echo "Usage: $0 get-fields <ISSUE_KEY>"; exit 1; fi
  check_auth

  curl -s -u "$JIRA_USER:$JIRA_PASS" "$JIRA_URL/rest/api/2/issue/$key/editmeta" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
for name, field in d.get('fields', {}).items():
    required = '✅' if field.get('required') else '  '
    ftype = field.get('schema', {}).get('type', '?')
    print(f'{required} {name:>25}  ({ftype})')
"
}

# Get the Epic list
get_epics() {
  local project_name="${1:-Example Product}"
  check_auth

  curl -s -u "$JIRA_USER:$JIRA_PASS" \
    "$JIRA_URL/rest/api/2/search?jql=project=%22$(echo "$project_name" | python3 -c "import sys,urllib.parse; print(urllib.parse.quote(sys.stdin.read()))")%22%20AND%20issuetype=Epic&maxResults=50" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
for issue in d.get('issues', []):
    print(f\"{issue['key']:>12}  {issue['fields'].get('summary', '')}\")
"
}

# List all projects
list_projects() {
  check_auth
  curl -s -u "$JIRA_USER:$JIRA_PASS" "$JIRA_URL/rest/api/2/project" \
    | python3 -c "
import sys, json
for p in json.load(sys.stdin):
    print(f\"{p['key']:>10}  {p['name']}\")
"
}

# Get available status transitions
get_transitions() {
  local key="$1"
  if [ -z "$key" ]; then echo "Usage: $0 get-transitions <ISSUE_KEY>"; exit 1; fi
  check_auth

  curl -s -u "$JIRA_USER:$JIRA_PASS" "$JIRA_URL/rest/api/2/issue/$key/transitions" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
for t in d.get('transitions', []):
    print(f\"  ID={t['id']:>4}  → {t['to']['name']}\")
"
}

# Status transition
transition() {
  local key="$1"
  local target="$2"
  local sprint_id="${3:-}"
  local design_hours="${4:-}"

  if [ -z "$key" ] || [ -z "$target" ]; then
    echo "Usage: $0 transition <ISSUE_KEY> <target_status> [sprint_id] [design_hours]"
    echo ""
    echo "Target status examples (must match your JIRA workflow): Done, In Progress, Reviewed, Not Started, Cancelled, Requirement Scheduled"
    exit 1
  fi
  check_auth

  # Get available transitions
  local transitions
  transitions=$(curl -s -u "$JIRA_USER:$JIRA_PASS" "$JIRA_URL/rest/api/2/issue/$key/transitions")

  # Match the target status
  local tid
  tid=$(echo "$transitions" | python3 -c "
import sys, json
target = '$target'.strip()
ts = json.load(sys.stdin).get('transitions', [])

# Match priority: exact name -> exact to.name -> name contains -> to.name contains
for t in ts:
    if t.get('name', '') == target:
        print(t['id']); sys.exit(0)
for t in ts:
    if t.get('to', {}).get('name', '') == target:
        print(t['id']); sys.exit(0)
for t in ts:
    if target in t.get('name', ''):
        print(t['id']); sys.exit(0)
for t in ts:
    if target in t.get('to', {}).get('name', ''):
        print(t['id']); sys.exit(0)
print('', file=sys.stderr)
sys.exit(1)
" 2>/dev/null)

  if [ -z "$tid" ]; then
    echo "❌ No status transition found to '$target'"
    echo "Available transitions:"
    echo "$transitions" | python3 -c "
import sys, json
for t in json.load(sys.stdin).get('transitions', []):
    print(f\"  ID={t['id']:>4}  → {t['to']['name']}\")
"
    exit 1
  fi

  # Optional: update the Sprint / design hours fields first
  if [ -n "$sprint_id" ] || [ -n "$design_hours" ]; then
    local project sprint_field design_hours_field
    project=$(get_issue_project "$key")
    sprint_field=$(workflow_field_key "$project" sprint "10004")
    design_hours_field=$(workflow_field_key "$project" design_hours "15700")

    local field_updates="{"
    [ -n "$sprint_id" ] && field_updates="$field_updates \"$sprint_field\": $sprint_id,"
    [ -n "$design_hours" ] && field_updates="$field_updates \"$design_hours_field\": $design_hours,"
    field_updates="${field_updates%,} }"

    curl -s -u "$JIRA_USER:$JIRA_PASS" -X PUT "$JIRA_URL/rest/api/2/issue/$key" \
      -H "Content-Type: application/json" \
      -d "{\"fields\": $field_updates}" > /dev/null
    echo "  Fields updated: sprint=${sprint_id:-unset}, design_hours=${design_hours:-unset}"
  fi

  # Perform the transition
  local resp
  resp=$(curl -s -u "$JIRA_USER:$JIRA_PASS" -X POST "$JIRA_URL/rest/api/2/issue/$key/transitions" \
    -H "Content-Type: application/json" \
    -d "{\"transition\": {\"id\": \"$tid\"}}")

  if [ -z "$resp" ]; then
    echo "✅ Status changed to: $target"
  elif echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if not d.get('errors') and not d.get('errorMessages') else 1)" 2>/dev/null; then
    echo "✅ Status changed to: $target"
  else
    echo "❌ Status change failed"
    echo "$resp" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for k, v in d.get('errors', {}).items():
        print(f'  {k}: {v}')
    for m in d.get('errorMessages', []):
        print(f'  {m}')
except:
    print(sys.stdin.read())
" 2>/dev/null || echo "$resp"
    exit 1
  fi
}

# Requirement scheduling
schedule() {
  local key="$1"
  local test_owner="$2"
  local est_test="$3"
  local est_release="$4"

  if [ -z "$key" ] || [ -z "$test_owner" ] || [ -z "$est_test" ] || [ -z "$est_release" ]; then
    echo "Usage: $0 schedule <ISSUE_KEY> <test_owner> <est_test_date> <est_release_date>"
    echo ""
    echo "Example: $0 schedule PROJ-123 alice 2026-05-08 2026-05-14"
    exit 1
  fi
  check_auth

  # Update the scheduling fields
  echo "📅 Updating scheduling fields..."
  local project test_owner_field est_release_field est_test_field payload
  project=$(get_issue_project "$key")
  test_owner_field=$(workflow_field_key "$project" test_owner "14301")
  est_release_field=$(workflow_field_key "$project" estimated_release_date "12500")
  est_test_field=$(workflow_field_key "$project" estimated_test_date "14303")

  payload=$(TEST_OWNER_FIELD="$test_owner_field" \
    EST_RELEASE_FIELD="$est_release_field" \
    EST_TEST_FIELD="$est_test_field" \
    TEST_OWNER="$test_owner" \
    EST_RELEASE="$est_release" \
    EST_TEST="$est_test" \
    python3 - <<'PY'
import json
import os

print(json.dumps({
    "fields": {
        os.environ["TEST_OWNER_FIELD"]: {"name": os.environ["TEST_OWNER"]},
        os.environ["EST_RELEASE_FIELD"]: os.environ["EST_RELEASE"],
        os.environ["EST_TEST_FIELD"]: os.environ["EST_TEST"],
    }
}, ensure_ascii=False))
PY
)

  curl -s -u "$JIRA_USER:$JIRA_PASS" -X PUT "$JIRA_URL/rest/api/2/issue/$key" \
    -H "Content-Type: application/json" \
    -d "$payload" > /dev/null
  echo "  ✅ Test owner: $test_owner"
  echo "  ✅ Estimated test submission: $est_test"
  echo "  ✅ Estimated release: $est_release"

  # Perform the "Requirement Scheduled" transition (name must match your JIRA workflow)
  echo ""
  transition "$key" "Requirement Scheduled"
}

# DingTalk notification
notify_dingtalk() {
  local title="$1"
  local content="$2"
  local webhook_token="${3:-}"
  local project_type="${4:-unknown}"

  if [ -z "$title" ] || [ -z "$content" ]; then
    echo "Usage: $0 notify-dingtalk <title> <content> [webhook_token] [project_type]"
    exit 1
  fi

  # If no webhook token was passed, look it up from .env
  if [ -z "$webhook_token" ]; then
    webhook_token="${DINGTALK_PROJ_WEBHOOK:-${DINGTALK_PLAT_WEBHOOK:-}}"
  fi

  if [ -z "$webhook_token" ]; then
    echo "❌ DingTalk webhook token not configured"
    echo "   Set DINGTALK_PROJ_WEBHOOK or DINGTALK_PLAT_WEBHOOK"
    exit 1
  fi

  local webhook="https://oapi.dingtalk.com/robot/send?access_token=$webhook_token"

  local payload
  payload=$(TITLE="$title" CONTENT="$content" python3 - <<'PY'
import json
import os

title = os.environ["TITLE"]
content = os.environ["CONTENT"]
print(json.dumps({
    'msgtype': 'markdown',
    'markdown': {
        'title': title,
        'text': f'### {title}\n\n{content}'
    }
}, ensure_ascii=False))
PY
)

  local result errcode
  result=$(curl -s -X POST "$webhook" -H "Content-Type: application/json" -d "$payload")
  errcode=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('errcode', -1))" 2>/dev/null)

  if [ "$errcode" = "0" ]; then
    echo "✅ DingTalk notification sent"
    record_notify_for_weekly "$title" "$content" "$webhook_token" "$project_type" "$result"
  else
    echo "❌ DingTalk notification failed: $result"
  fi
}

jira_json_field() {
  local field="$1"
  local mode="${2:-string}"
  FIELD="$field" MODE="$mode" python3 -c '
import json
import os
import sys

data = json.load(sys.stdin)
fields = data.get("fields", {})
value = fields.get(os.environ["FIELD"])
mode = os.environ.get("MODE", "string")

def text(v):
    if v is None:
        return ""
    return str(v)

if mode == "user":
    if isinstance(value, dict):
        print(value.get("name") or value.get("displayName") or "")
    else:
        print("")
elif mode == "array_value":
    first = value[0] if isinstance(value, list) and value else None
    if isinstance(first, dict):
        print(first.get("value") or first.get("name") or first.get("id") or "")
    else:
        print(text(first))
elif mode == "object_value":
    if isinstance(value, dict):
        print(value.get("value") or value.get("name") or value.get("id") or "")
    else:
        print(text(value))
else:
    print(text(value))
'
}

# Read information from JIRA and Confluence and send a notification
notify_story() {
  local jira_key="$1"
  local confluence_id="${2:-}"
  local project_type="${3:-main}"
  local project_type_upper
  project_type_upper=$(echo "$project_type" | tr '[:lower:]' '[:upper:]')

  if [ -z "$jira_key" ]; then
    echo "Usage: $0 notify-story <JIRA_KEY> [confluence_page_id] [main|plat]"
    exit 1
  fi
  check_auth

  # Get the webhook token
  local webhook_env_var="DINGTALK_${project_type_upper}_WEBHOOK"
  local webhook_token="${!webhook_env_var:-}"

  if [ -z "$webhook_token" ]; then
    echo "❌ DingTalk webhook token not configured: $webhook_env_var"
    echo "   Configure it in .env or pass it via an environment variable"
    exit 1
  fi

  # Read JIRA information
  local jira_data project need_user_field center_source_field region_source_field req_type_field compliance_field epic_field
  project=$(get_issue_project "$jira_key")
  need_user_field=$(field_key_or_default "$project" need_user "customfield_11700")
  center_source_field=$(field_key_or_default "$project" center_source "customfield_14700")
  region_source_field=$(field_key_or_default "$project" region_source "customfield_16100")
  req_type_field=$(field_key_or_default "$project" req_type "customfield_14305")
  compliance_field=$(field_key_or_default "$project" compliance "customfield_14602")
  epic_field=$(field_key_or_default "$project" epic_link "customfield_10000")

  jira_data=$(curl -s -u "$JIRA_USER:$JIRA_PASS" \
    "$JIRA_URL/rest/api/2/issue/$jira_key?fields=summary,description,$need_user_field,$center_source_field,$region_source_field,$req_type_field,$compliance_field,$epic_field")

  local summary desc need_user center_source region_source req_type compliance epic
  summary=$(echo "$jira_data" | jira_json_field summary string 2>/dev/null)
  desc=$(echo "$jira_data" | jira_json_field description string 2>/dev/null | sed 's/<[^>]*>//g' | tr '\n' ' ' | cut -c1-200)
  need_user=$(echo "$jira_data" | jira_json_field "$need_user_field" user 2>/dev/null)
  center_source=$(echo "$jira_data" | jira_json_field "$center_source_field" array_value 2>/dev/null)
  region_source=$(echo "$jira_data" | jira_json_field "$region_source_field" object_value 2>/dev/null)
  req_type=$(echo "$jira_data" | jira_json_field "$req_type_field" array_value 2>/dev/null)
  compliance=$(echo "$jira_data" | jira_json_field "$compliance_field" object_value 2>/dev/null)
  epic=$(echo "$jira_data" | jira_json_field "$epic_field" string 2>/dev/null)

  # Read Confluence background
  local confluence_bg="None"
  if [ -z "$confluence_id" ]; then
    confluence_id=$(echo "$desc" | grep -o 'pageId=[0-9]*' | head -1 | cut -d= -f2)
  fi
  if [ -n "$confluence_id" ] && [ -n "${CONFLUENCE_URL:-}" ]; then
    confluence_bg=$(curl -s -u "$JIRA_USER:$JIRA_PASS" \
      "${CONFLUENCE_URL:-http://your-domain.atlassian.net/wiki:8090}/rest/api/content/$confluence_id?expand=body.storage" \
      | python3 -c "import sys,json; v=json.load(sys.stdin).get('body',{}).get('storage',{}).get('value',''); print(v)" 2>/dev/null \
      | sed 's/<[^>]*>//g' | tr '\n' ' ' | cut -c1-100)
  fi

  # Build the notification content
  local dingtalk_content
  dingtalk_content=$(cat << DINGEOF
### 📝 Background

$confluence_bg

---
### 📌 Requirement Info

| Item | Content |
|:---|:---|
| **Requester** | 👤 $need_user |
| **Epic** | 🎯 $epic |
| **Requirement type** | 📦 $req_type |
| **Compliance involved** | ✅ $compliance |

---
### 🔗 Document Links

- **JIRA:** [$jira_key]($JIRA_URL/browse/$jira_key)
- **Requirements doc:** [Confluence]($CONFLUENCE_URL/pages/viewpage.action?pageId=$confluence_id)
DINGEOF
)

  notify_dingtalk "📋 $summary" "$dingtalk_content" "$webhook_token" "$project_type"
}

# ── Help ──────────────────────────────────

show_help() {
  cat << 'HELP'
JIRA API Wrapper v2.0 (config-driven)

Usage: jira.sh <command> [arguments]

── Create and manage ──
  create-story    Create a Story (generic)
    --project <PROJ|PLAT> --summary "Title" [other options]
  get-issue       <KEY>                  Show Issue details
  get-confluence-url <KEY> [text|json]  Parse Confluence link / pageId from the description
  append-description <KEY> '<wiki>'     Append a Wiki block to the description (write back links)
  search          <JQL> [max]            JQL search
  get-fields      <KEY>                  Show editable fields
  get-transitions <KEY>                  Show available status transitions
  transition      <KEY> <target_status> [sprint] [hours]  Status transition
  schedule        <KEY> <Owner> <test> <release>     Requirement scheduling

── Query ──
  get-epics       [project name]          List Epics
  list-projects                          List all projects

── Notifications ──
  notify-dingtalk <title> <content> [token] <type>  Send a DingTalk notification
  notify-story    <KEY> [pageId] [main|plat]     Read from JIRA and notify

Examples:
  # Create a PROJ Story (using defaults)
  jira.sh create-story --project PROJ --summary "[Module B] New feature" \
    --need-user <requester-username> --background "Improve efficiency"

  # Create an PLAT Story
  jira.sh create-story --project PLAT --summary "[Platform] XX management" \
    --need-user bob --center-source "Center B"

  # Status change
  jira.sh transition PROJ-123 Done
  jira.sh transition PLAT-2 Reviewed 902 8

  # Scheduling
  jira.sh schedule PROJ-123 alice 2026-05-08 2026-05-14

  # Search my Stories
  jira.sh search "project=PROJ AND assignee=currentuser()"

  # Send a notification
  jira.sh notify-story PROJ-123 123456 main

Configuration:
  Credentials (domain account first): JIRA_USERNAME / JIRA_PASSWORD, or JIRA_USER / JIRA_PASS in .env
  Projects: the projects node in config.yaml
HELP
}

# ── Main entry ────────────────────────────────

case "${1:-help}" in
  create-story)       shift; create_story "$@" ;;
  get-issue)          get_issue "${2:-}" ;;
  get-confluence-url) get_confluence_url "${2:-}" "${3:-text}" ;;
  search)             search_issues "${2:-}" "${3:-20}" ;;
  get-fields)         get_fields "${2:-}" ;;
  get-transitions)    get_transitions "${2:-}" ;;
  transition)         transition "${2:-}" "${3:-}" "${4:-}" "${5:-}" ;;
  schedule)           schedule "${2:-}" "${3:-}" "${4:-}" "${5:-}" ;;
  append-description) append_description "${2:-}" "${3:-}" ;;
  get-epics)          get_epics "${2:-Example Product}" ;;
  list-projects)      list_projects ;;
  notify-dingtalk)    notify_dingtalk "${2:-}" "${3:-}" "${4:-}" "${5:-}" ;;
  notify-story)       notify_story "${2:-}" "${3:-}" "${4:-}" ;;
  help|--help|-h)     show_help ;;
  *)
    echo "Unknown command: ${1:-}"
    echo "Run '$0 help' for usage"
    exit 1
    ;;
esac
