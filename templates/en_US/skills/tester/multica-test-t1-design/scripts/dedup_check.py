#!/usr/bin/env python3
"""
Dedup Check - compare against existing Jira cases and remove duplicates.

Usage:
  python scripts/dedup_check.py \\
    --jira-url https://your-domain.atlassian.net/browse/PROJ-123 \\
    --input proposed_test_cases.json \\
    --output deduped_test_cases.json

Features:
  1. Fetch existing test cases under the Jira requirement (subtasks / linked issues)
  2. For each new case, fuzzy-match against existing cases by title + steps
  3. Flag duplicates and give a similarity score
  4. Output the deduplicated case list

Environment variables:
  JIRA_EMAIL, JIRA_API_TOKEN  - Cloud Jira authentication
  JIRA_COOKIE                 - self-hosted Jira authentication (e.g. JSESSIONID=xxx)
"""

import argparse
import json
import os
import re
import sys
# Fix Windows terminal encoding for non-ASCII output
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from base64 import b64encode
from difflib import SequenceMatcher
from urllib.parse import urlparse

try:
    import local_env  # noqa: F401  - loads config.local.env
except ImportError:
    pass

try:
    import requests
except ImportError:
    print('Missing requests library; run: pip install requests', file=sys.stderr)
    sys.exit(1)


# ============================================================
# JQL / API Constants
# ============================================================

# Common test-case issue type names. The non-ASCII entries are Chinese Jira issue type names
# (kept as \u escapes because they must match the localized Jira instance):
#   \u6d4b\u8bd5\u7528\u4f8b = "test case", \u6d4b\u8bd5 = "test", \u5b50\u4efb\u52a1 = "subtask"
TEST_ISSUE_TYPES = {"Test", "\u6d4b\u8bd5\u7528\u4f8b", "\u6d4b\u8bd5", "Sub-test", "Subtask", "\u5b50\u4efb\u52a1"}


# ============================================================
# Auth & API
# ============================================================

def get_rest_path() -> str:
    return "/rest/api/2" if ("JIRA_COOKIE" in os.environ or "JIRA_USERNAME" in os.environ) else "/rest/api/3"


def build_auth_headers() -> dict:
    """Pick the auth method from environment variables (username/password first, since cookies expire)."""
    headers = {"Accept": "application/json"}

    username = os.environ.get("JIRA_USERNAME")
    password = os.environ.get("JIRA_PASSWORD")
    if username and password:
        b = b64encode(f"{username}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {b}"
        return headers

    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")
    if email and api_token:
        b = b64encode(f"{email}:{api_token}".encode()).decode()
        headers["Authorization"] = f"Basic {b}"
        return headers

    cookie = os.environ.get("JIRA_COOKIE")
    if cookie:
        headers["Cookie"] = cookie
        return headers

    print(
        "Please configure authentication (prefer Windows system environment variables JIRA_USERNAME / JIRA_PASSWORD; config.local.env is an optional fallback):\n"
        "  copy config.local.env.example -> config.local.env and fill it in",
        file=sys.stderr,
    )
    sys.exit(1)


def parse_jira_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    m = re.search(r'/browse/([A-Z]+-\d+)', parsed.path)
    if not m:
        raise ValueError(f"Unable to parse Jira URL: {url}")
    return base, m.group(1)


def jira_get(base: str, path: str, auth: dict) -> dict:
    """Call the Jira API, auto-adapting to /rest/api/2 or /rest/api/3."""
    rest_path = get_rest_path()
    url = f"{base}{rest_path}{path}" if not path.startswith("/rest/") else f"{base}{path}"
    resp = requests.get(url, headers=auth, timeout=30)
    if resp.status_code == 401:
        print("Authentication failed: check JIRA_USERNAME+JIRA_PASSWORD, or JIRA_COOKIE, or JIRA_EMAIL+JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


# ============================================================
# Fetch existing test cases
# ============================================================

def fetch_existing_test_cases(base_url: str, parent_key: str, auth: dict) -> list[dict]:
    """
    Use JQL to find test cases among all subtasks / linked issues of the requirement.
    Strategy:
      1. Query subtasks where parent = parent_key
      2. Query issues linked to parent_key via issueLink whose type is Test
    """
    existing = {}

    # Strategy 1: subtasks
    jql = f'parent = "{parent_key}" ORDER BY created'
    data = jira_get(base_url, f"/search?jql={requests.utils.quote(jql)}&maxResults=200&fields=summary,description,issuetype,customfield_*", auth)
    for issue in data.get("issues", []):
        key = issue["key"]
        fields = issue.get("fields", {})
        existing[key] = {
            "key": key,
            "summary": fields.get("summary", ""),
            "description": fields.get("description", "") or "",
            "issue_type": fields.get("issuetype", {}).get("name", ""),
            "source": "subtask",
        }

    # Strategy 2: test cases linked via issue link
    jql = (
        f'issue in linkedIssues("{parent_key}") '
        f'AND issuetype in ("Test", "\u6d4b\u8bd5\u7528\u4f8b", "\u6d4b\u8bd5") '
        f'ORDER BY created'
    )
    data = jira_get(base_url, f"/search?jql={requests.utils.quote(jql)}&maxResults=200&fields=summary,description", auth)
    for issue in data.get("issues", []):
        key = issue["key"]
        if key not in existing:
            fields = issue.get("fields", {})
            existing[key] = {
                "key": key,
                "summary": fields.get("summary", ""),
                "description": fields.get("description", "") or "",
                "issue_type": fields.get("issuetype", {}).get("name", ""),
                "source": "link",
            }

    return list(existing.values())


# ============================================================
# Text similarity
# ============================================================

def normalize(text: str) -> str:
    """Normalize text for comparison."""
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)  # keep only CJK characters, letters, digits
    return text.lower().strip()


def title_similarity(t1: str, t2: str) -> float:
    """Title similarity (0~1)."""
    n1, n2 = normalize(t1), normalize(t2)
    if not n1 or not n2:
        return 0.0
    return SequenceMatcher(None, n1, n2).ratio()


def keyword_overlap(t1: str, t2: str) -> float:
    """Keyword overlap ratio - catches cases with the same functional keywords but different wording."""
    # Tokenize: split on anything that is not a letter, digit or CJK character
    def tokenize(s):
        return set(re.findall(r'[\w\u4e00-\u9fff]+', normalize(s)))
    tok1, tok2 = tokenize(t1), tokenize(t2)
    if not tok1 or not tok2:
        return 0.0
    intersection = tok1 & tok2
    return len(intersection) / max(len(tok1), len(tok2))


def compute_similarity(proposed: dict, existing: dict) -> float:
    """
    Compute the overall similarity of two cases.
    Considers: title + steps/description
    """
    p_title = proposed.get("title", "")
    p_steps = " ".join(proposed.get("steps", []))
    p_text = p_title + " " + p_steps
    if proposed.get("expected_results"):
        p_text += " " + " ".join(proposed["expected_results"])

    e_summary = existing.get("summary", "")
    e_desc = existing.get("description", "")

    # Title similarity weight 0.6
    title_sim = title_similarity(p_title, e_summary)
    kw_sim = keyword_overlap(p_title, e_summary)

    # Content similarity weight 0.4
    content_sim = title_similarity(p_text, e_summary + " " + e_desc)

    # Combined score
    score = max(title_sim, kw_sim) * 0.6 + content_sim * 0.4
    return score


# ============================================================
# Main dedup logic
# ============================================================

# Similarity thresholds
SIMILARITY_HIGH = 0.75   # highly similar -> skip automatically
SIMILARITY_MEDIUM = 0.50  # moderately similar -> flag for human confirmation


def dedup(proposed: list[dict], existing: list[dict]) -> dict:
    """
    Return the dedup result:
      - new: new cases with no duplicates
      - skipped: cases skipped automatically due to high similarity (with the matched existing case)
      - ambiguous: moderately similar cases that need human confirmation
    """
    new_list = []
    skipped_list = []
    ambiguous_list = []

    for tc in proposed:
        best_match = None
        best_score = 0.0

        for et in existing:
            score = compute_similarity(tc, et)
            if score > best_score:
                best_score = score
                best_match = et

        entry = {
            "test_case": tc,
            "best_match": best_match,
            "similarity": round(best_score, 3),
        }

        if best_score >= SIMILARITY_HIGH:
            entry["reason"] = f"{best_score:.0%} similar to {best_match['key']}, skipped automatically"
            skipped_list.append(entry)
        elif best_score >= SIMILARITY_MEDIUM:
            entry["reason"] = f"{best_score:.0%} similar to {best_match['key']}, confirm whether it is a duplicate"
            ambiguous_list.append(entry)
        else:
            new_list.append(entry)

    return {
        "new": new_list,
        "skipped": skipped_list,
        "ambiguous": ambiguous_list,
        "summary": {
            "total_proposed": len(proposed),
            "new": len(new_list),
            "skipped": len(skipped_list),
            "ambiguous": len(ambiguous_list),
        },
    }


# ============================================================
# Entry point
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Test-case dedup check")
    parser.add_argument("--jira-url", required=True, help="Full URL of the Jira requirement")
    parser.add_argument("--input", "-i", required=True, help="JSON file of newly generated test cases")
    parser.add_argument("--output", "-o", default="deduped_test_cases.json", help="Output file after dedup")
    parser.add_argument("--dry-run", action="store_true", help="Only print the dedup report; do not write an output file")
    args = parser.parse_args()

    # Auth check
    cookie = os.environ.get("JIRA_COOKIE")
    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")
    username = os.environ.get("JIRA_USERNAME")
    password = os.environ.get("JIRA_PASSWORD")
    if not cookie and not (email and api_token) and not (username and password):
        print(
            "Please configure authentication (prefer Windows system environment variables JIRA_USERNAME / JIRA_PASSWORD; config.local.env is an optional fallback):\n"
            "  copy config.local.env.example -> config.local.env and fill it in",
            file=sys.stderr,
        )
        sys.exit(1)

    auth = build_auth_headers()
    base_url, parent_key = parse_jira_url(args.jira_url)

    # Read the new cases
    with open(args.input, "r", encoding="utf-8") as f:
        proposed = json.load(f)

    # If the input is a dict containing key "test_cases" or "functional"/"api"
    if isinstance(proposed, dict):
        for key in ("test_cases", "functional", "api", "cases"):
            if key in proposed and isinstance(proposed[key], list):
                proposed = proposed[key]
                break

    print(f"\nCases to check: {len(proposed)}", file=sys.stderr)

    # Fetch existing cases
    print(f"Fetching existing test cases under {parent_key}...", file=sys.stderr)
    existing = fetch_existing_test_cases(base_url, parent_key, auth)
    print(f"Existing test cases: {len(existing)}", file=sys.stderr)

    if existing:
        print("\nExisting case list:", file=sys.stderr)
        for et in existing:
            print(f"  {et['key']}: {et['summary'][:60]}", file=sys.stderr)

    # Dedup
    print("\nDeduplicating...", file=sys.stderr)
    result = dedup(proposed, existing)

    # Report
    s = result["summary"]
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"Dedup report:", file=sys.stderr)
    print(f"  Total: {s['total_proposed']}", file=sys.stderr)
    print(f"  New: {s['new']}", file=sys.stderr)
    print(f"  Skipped: {s['skipped']} (similarity >= {SIMILARITY_HIGH:.0%})", file=sys.stderr)
    print(f"  Ambiguous: {s['ambiguous']} (similarity {SIMILARITY_MEDIUM:.0%} ~ {SIMILARITY_HIGH:.0%})", file=sys.stderr)
    print(f"{'='*50}", file=sys.stderr)

    if result["skipped"]:
        print("\nSkipped automatically:", file=sys.stderr)
        for item in result["skipped"]:
            tc = item["test_case"]
            print(f"  x [{item['similarity']:.0%}] {tc.get('title', tc.get('case_id', ''))}", file=sys.stderr)
            print(f"    Matched: {item['best_match']['key']} - {item['best_match']['summary'][:50]}", file=sys.stderr)

    if result["ambiguous"]:
        print("\nNeeds human confirmation:", file=sys.stderr)
        for item in result["ambiguous"]:
            tc = item["test_case"]
            print(f"  ? [{item['similarity']:.0%}] {tc.get('title', tc.get('case_id', ''))}", file=sys.stderr)
            print(f"    Matched: {item['best_match']['key']} - {item['best_match']['summary'][:50]}", file=sys.stderr)

    if not args.dry_run:
        # Output only the cases confirmed as new
        new_cases = [item["test_case"] for item in result["new"]]
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(new_cases, f, ensure_ascii=False, indent=2)
        print(f"\nDeduplicated cases saved: {args.output}", file=sys.stderr)

    # Print the dedup result JSON to stdout (for downstream scripts)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
