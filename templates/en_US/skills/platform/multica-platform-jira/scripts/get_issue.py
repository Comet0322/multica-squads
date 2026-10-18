#!/usr/bin/env python3
"""
JIRA Issue reader (platform) — fetch issue JSON with Confluence/Figma link extraction.

Usage:
  python scripts/get_issue.py --url https://your-domain.atlassian.net/browse/PROJ-123
  python scripts/get_issue.py --url https://your-domain.atlassian.net/browse/PROJ-123 --output data/jira_issue.json
  python scripts/jira_cli.py get-issue --url https://... --output data/jira_issue.json

Authentication config (local file preferred; Multica environment variables are not required):
  <skill>/config.local.env  - recommended; copy from config.local.env.example and fill in
  or process environment variables:
  JIRA_EMAIL / JIRA_API_TOKEN / JIRA_COOKIE / JIRA_USERNAME / JIRA_PASSWORD, etc.

Output:
  - stdout or file: Issue information as JSON (including extracted Confluence/Figma links)
"""

import argparse
import json
import os
import re
import sys
# Fix Windows terminal encoding for Chinese output
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from base64 import b64encode
from urllib.parse import urlparse, parse_qs
from html import unescape

try:
    import local_env  # noqa: F401  - loads config.local.env
except ImportError:
    pass

try:
    import requests
except ImportError:
    print('Missing the requests library; run: pip install requests', file=sys.stderr)
    sys.exit(1)


# ============================================================
# Link matching patterns
# ============================================================

PATTERN_CONFLUENCE = re.compile(
    r'https?://[^/\s]+(?:\.atlassian\.net)[^\]"\'()\s]*(?:wiki/|pages/)[^\s)"\'>]+'
)
PATTERN_FIGMA = re.compile(
    r'https?://[^/\s]+\.figma\.com/(?:file|design|proto)/([a-zA-Z0-9]+)[^\s)""\'>]*'
)


# ============================================================
# Jira API calls
# ============================================================

def is_self_hosted(url: str) -> bool:
    """Detect whether this is a self-hosted Jira (not atlassian.net)"""
    parsed = urlparse(url)
    return 'atlassian.net' not in parsed.netloc

def get_rest_path() -> str:
    return "/rest/api/2" if ("JIRA_COOKIE" in os.environ or "JIRA_USERNAME" in os.environ or "JIRA_USERNAME" in os.environ) else "/rest/api/3"

def build_auth_headers() -> dict:
    """Choose the authentication method automatically from environment variables (username/password preferred, to avoid expired cookies)"""
    headers = {"Accept": "application/json"}

    username = os.environ.get("JIRA_USERNAME")
    password = os.environ.get("JIRA_PASSWORD")
    if username and password:
        b = b64encode(f"{username}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {b}"
        return headers

    # Domain account authentication (same priority as JIRA_USERNAME/JIRA_PASSWORD)
    domain_user = os.environ.get("JIRA_USERNAME")
    domain_pass = os.environ.get("JIRA_PASSWORD")
    if domain_user and domain_pass:
        b = b64encode(f"{domain_user}:{domain_pass}".encode()).decode()
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
        "Please configure authentication (local file recommended; Multica does not need a Secret):\n"
        "  1) Copy config.local.env.example -> config.local.env and fill it in\n"
        "  2) Or set environment variables:\n"
        "     Self-hosted: JIRA_USERNAME+PASSWORD or JIRA_USERNAME+PASSWORD\n"
        "     Cloud:  JIRA_EMAIL + JIRA_API_TOKEN",
        file=sys.stderr,
    )
    sys.exit(1)


def parse_jira_url(url: str) -> tuple[str, str]:
    """Parse base_url and issue_key from a Jira URL"""
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    # URL looks like: https://xx.atlassian.net/browse/PROJ-123 or http://your-domain.atlassian.net:8080/browse/PROJ-123
    match = re.search(r'/browse/([A-Z]+-\d+)', parsed.path)
    if not match:
        raise ValueError(f"Could not parse the Issue Key from the URL: {url}")
    return base_url, match.group(1)


def fetch_issue(base_url: str, issue_key: str, auth_headers: dict) -> dict:
    """Fetch Jira Issue details (including attachments, rendered fields, issuelinks)"""
    rest_path = get_rest_path()
    url = f"{base_url}{rest_path}/issue/{issue_key}"
    resp = requests.get(
        url,
        headers=auth_headers,
        params={
            "expand": "renderedFields",
            "fields": "summary,description,issuetype,status,priority,attachment,issuelinks",
        },
        timeout=30,
    )
    if resp.status_code == 401:
        print("Authentication failed: check JIRA_USERNAME+JIRA_PASSWORD, JIRA_COOKIE, or JIRA_EMAIL+JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)
    if resp.status_code == 404:
        print(f"Issue does not exist: {issue_key}", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


# ============================================================
# Text extraction
# ============================================================

def extract_text_from_adf(adf: dict | str | None) -> str:
    """Recursively extract plain text from Atlassian Document Format"""
    if adf is None:
        return ""
    if isinstance(adf, str):
        return adf
    texts = []
    if isinstance(adf, dict):
        if adf.get("type") == "text" and "text" in adf:
            texts.append(adf["text"])
        for key in ("content", "items", "args"):
            child = adf.get(key)
            if isinstance(child, list):
                for item in child:
                    texts.append(extract_text_from_adf(item))
            elif isinstance(child, dict):
                texts.append(extract_text_from_adf(child))
    return " ".join(texts)


def extract_text_with_structure(adf: dict | str | None) -> str:
    """Extract structured Markdown text from ADF (preserving tables, lists, formatting, etc.)

    Unlike extract_text_from_adf, this function preserves the structural information in ADF (table rows and columns, list levels,
    formatting marks) and outputs Markdown rather than concatenated plain text.
    """
    if adf is None:
        return ""
    if isinstance(adf, str):
        return adf

    result_parts = []

    def process_node(node: dict, indent: str = "") -> str:
        """Recursively process an ADF node and return Markdown text"""
        if not isinstance(node, dict):
            return str(node) if node is not None else ""

        node_type = node.get("type", "")
        content = node.get("content") or []
        text_val = node.get("text", "")
        marks = node.get("marks") or []
        attrs = node.get("attrs") or {}

        # Text node
        if node_type == "text" and text_val:
            formatted = text_val
            for mark in marks:
                mark_type = mark.get("type", "")
                if mark_type == "strong":
                    formatted = f"**{formatted}**"
                elif mark_type == "em":
                    formatted = f"*{formatted}*"
                elif mark_type == "code":
                    formatted = f"`{formatted}`"
                elif mark_type == "strike":
                    formatted = f"~~{formatted}~~"
                elif mark_type == "underline":
                    formatted = f"<u>{formatted}</u>"
                elif mark_type == "link":
                    href = mark.get("attrs", {}).get("href", "")
                    formatted = f"[{formatted}]({href})"
                elif mark_type == "subsup":
                    type_ = mark.get("attrs", {}).get("type", "")
                    formatted = f"^{formatted}^" if type_ == "sup" else f"~{formatted}~"
            return formatted

        # Paragraph
        if node_type == "paragraph":
            inner = "".join(process_node(c) for c in content)
            return f"\n\n{inner}\n\n" if inner.strip() else ""

        # Heading
        if node_type.startswith("heading"):
            level = attrs.get("level", 1)
            inner = "".join(process_node(c) for c in content)
            return f"\n\n{'#' * level} {inner}\n\n"

        # List
        if node_type == "bulletList":
            items = []
            for c in content:
                item_text = process_node(c, indent + "  ")
                items.append(f"{indent}- {item_text.strip()}")
            return "\n" + "\n".join(items) + "\n"

        if node_type == "orderedList":
            order = attrs.get("order", 1)
            items = []
            for i, c in enumerate(content):
                item_text = process_node(c, indent + "   ")
                items.append(f"{indent}{order + i}. {item_text.strip()}")
            return "\n" + "\n".join(items) + "\n"

        if node_type == "listItem":
            inner = "".join(process_node(c, indent) for c in content)
            return inner

        # Table
        if node_type == "table":
            rows = []
            for c in content:
                row_text = process_node(c)
                if row_text:
                    rows.append(row_text)

            if not rows:
                return "\n\n[empty table]\n\n"

            # The first row is the header
            header_cells = rows[0].split("|")
            col_count = len(header_cells) - 2 if len(header_cells) > 2 else 3

            md = "\n\n" + rows[0] + "\n"
            md += "| " + " | ".join(["---"] * col_count) + " |\n"
            md += "\n".join(rows[1:]) + "\n\n"
            return md

        if node_type == "tableRow":
            cells = []
            for c in content:
                cell_text = process_node(c)
                cells.append(cell_text)
            return "| " + " | ".join(cells) + " |"

        if node_type == "tableHeader" or node_type == "tableCell":
            inner = "".join(process_node(c) for c in content)
            return inner.strip()

        # Code block
        if node_type == "codeBlock":
            lang = attrs.get("language", "")
            inner = "".join(process_node(c) for c in content)
            return f"\n```{lang}\n{inner}\n```\n"

        # Blockquote
        if node_type == "blockquote":
            inner = "".join(process_node(c) for c in content)
            lines = inner.strip().split("\n")
            quoted = "\n".join(f"> {line}" for line in lines)
            return f"\n\n{quoted}\n\n"

        # Divider
        if node_type == "rule":
            return "\n\n---\n\n"

        # Hard line break
        if node_type == "hardBreak":
            return "\n"

        # Inline card (usually used for link previews)
        if node_type == "inlineCard":
            url = attrs.get("url", "")
            return f" [{url}] " if url else " [link] "

        # Media / image
        if node_type == "media":
            url = attrs.get("url", "")
            id_ = attrs.get("id", "")
            collection = attrs.get("collection", "")
            alt = ""
            for m in marks:
                if m.get("type") == "link":
                    alt_parts = []
                    for link_c in m.get("attrs", {}).get("href", ""):
                        alt_parts.append(str(link_c))
            return f"\n![image: {id_}](id:{id_})\n" if id_ else ""

        if node_type == "mediaGroup":
            inner = "".join(process_node(c) for c in content)
            return f"\n[media group]\n{inner}\n[/media group]\n"

        if node_type == "mediaSingle":
            inner = "".join(process_node(c) for c in content)
            return f"\n{inner}\n"

        # Task list
        if node_type == "taskList":
            inner = "".join(process_node(c, indent) for c in content)
            return f"\n{inner}\n"

        if node_type == "taskItem":
            state = attrs.get("state", "TODO")
            check = "[x]" if state == "DONE" else "[ ]"
            inner = "".join(process_node(c, indent) for c in content)
            return f"{indent}- {check} {inner.strip()}\n"

        # Decision list
        if node_type == "decisionList":
            inner = "".join(process_node(c, indent) for c in content)
            return f"\n{inner}\n"

        if node_type == "decisionItem":
            inner = "".join(process_node(c, indent) for c in content)
            return f"{indent}- 💡 {inner.strip()}\n"

        # Panel / container (similar to a Confluence info panel)
        if node_type == "panel":
            panel_type = attrs.get("panelType", "info")
            inner = "".join(process_node(c) for c in content)
            return f"\n> **[{panel_type.upper()}]** {inner}\n"

        # Expand / collapse
        if node_type == "expand":
            title = attrs.get("title", "Expand")
            inner = "".join(process_node(c) for c in content)
            return f"\n<details><summary>{title}</summary>\n{inner}\n</details>\n"

        # Nested content (recursively process content)
        inner = "".join(process_node(c, indent) for c in content)
        return inner

    for node in content if isinstance(content, list) else []:
        part = process_node(node)
        if part:
            result_parts.append(part)

    text = "".join(result_parts)
    # Clean up extra blank lines
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip()


def extract_links_from_text(text: str) -> dict:
    """Extract Confluence and Figma links from text"""
    # Jira description may contain HTML encoding
    text = unescape(text)
    confluence_links = list(set(PATTERN_CONFLUENCE.findall(text)))
    figma_links = list(set(PATTERN_FIGMA.findall(text)))
    # Deduplicate and assemble the complete links
    figma_full = []
    for fl in figma_links:
        # fl may be a file key or a partial URL; rebuild it
        full_links = PATTERN_FIGMA.findall(text)
        # Use the original match to get the complete link
        figma_full = list(set(PATTERN_FIGMA.findall(text)))

    # Re-match the complete Figma URL
    figma_urls = list(set(re.findall(
        r'https?://[^/\s]+\.figma\.com/(?:file|design|proto)/[a-zA-Z0-9]+[^\s)""\'>]*',
        text
    )))

    return {
        "confluence_links": confluence_links,
        "figma_links": figma_urls,
    }


def get_custom_field_value(field_value) -> str:
    """Extract a string from the various possible formats of a custom field"""
    if isinstance(field_value, dict):
        return field_value.get("value", field_value.get("name", ""))
    if isinstance(field_value, list):
        return ", ".join(get_custom_field_value(v) for v in field_value)
    if isinstance(field_value, str):
        return field_value
    return str(field_value) if field_value else ""


# ============================================================
# Linked Issues
# ============================================================

def extract_linked_issues(fields: dict) -> list:
    """Extract linked Issue summaries from the issuelinks field"""
    linked = []
    for link in fields.get("issuelinks") or []:
        link_type = link.get("type") or {}
        type_name = link_type.get("name", "")
        if link.get("inwardIssue"):
            direction = "inward"
            issue_ref = link["inwardIssue"]
            rel = link_type.get("inward", "")
        elif link.get("outwardIssue"):
            direction = "outward"
            issue_ref = link["outwardIssue"]
            rel = link_type.get("outward", "")
        else:
            continue
        issue_fields = issue_ref.get("fields") or {}
        status_obj = issue_fields.get("status") or {}
        linked.append({
            "key": issue_ref.get("key", ""),
            "summary": issue_fields.get("summary", ""),
            "status": status_obj.get("name", ""),
            "link_type": type_name,
            "relation": rel,
            "direction": direction,
        })
    return linked


def fetch_linked_issue_details(
    base_url: str, auth_headers: dict, linked_keys: list[str]
) -> list:
    """Fetch one more level of description and links for each linked KEY (one level only, to avoid an explosion of requests)"""
    details = []
    seen = set()
    for key in linked_keys:
        if not key or key in seen:
            continue
        seen.add(key)
        try:
            issue_data = fetch_issue(base_url, key, auth_headers)
            brief = process_issue(issue_data, fetch_linked=False)
            details.append({
                "key": brief["key"],
                "summary": brief["summary"],
                "status": brief["status"],
                "description_text": brief["description_text"],
                "links": brief["links"],
            })
        except Exception as exc:
            details.append({"key": key, "error": str(exc)})
    return details


# ============================================================
# Main flow
# ============================================================

def process_issue(issue_data: dict, fetch_linked: bool = False, base_url: str = "", auth_headers: dict | None = None) -> dict:
    """Process Issue data and extract key information"""
    fields = issue_data.get("fields", {})

    # Basic info
    summary = fields.get("summary", "")
    desc = fields.get("description")

    # Get the HTML-rendered description (from renderedFields)
    rendered_fields = issue_data.get("renderedFields", {})
    rendered_desc = rendered_fields.get("description", "")

    # description may be ADF or a plain string
    if isinstance(desc, str):
        description_text = desc
        description_html = desc
        adf_content = None
    else:
        description_text = extract_text_from_adf(desc)
        description_html = extract_text_with_structure(desc)  # structured Markdown
        adf_content = desc  # keep the original ADF structure

    # If renderedFields has an HTML description, Jira provides its own HTML-rendered version
    # This is more accurate than our ADF parsing (especially for tables, embedded content, etc.)
    if rendered_desc:
        description_html = f"{description_html}\n\n---\n\n### Jira Rendered HTML:\n\n{rendered_desc}"

    # Type, status, priority
    issue_type = fields.get("issuetype", {}).get("name", "")
    status = fields.get("status", {}).get("name", "")
    priority = fields.get("priority", {}).get("name", "")

    # Extract links
    all_text = f"{summary}\n{description_text}"
    links = extract_links_from_text(all_text)

    # Extract images from attachments
    attachments = fields.get("attachment", [])
    image_attachments = []
    for att in attachments:
        mime = att.get("mimeType", "")
        if mime.startswith("image/"):
            image_attachments.append({
                "id": att.get("id", ""),
                "filename": att.get("filename", ""),
                "mimeType": mime,
                "size": att.get("size", 0),
                "content_url": att.get("content", ""),  # download URL
                "thumbnail_url": att.get("thumbnail", ""),  # thumbnail URL
            })

    linked_issues = extract_linked_issues(fields)

    # Build the result
    result = {
        "key": issue_data.get("key", ""),
        "summary": summary,
        "issue_type": issue_type,
        "status": status,
        "priority": priority,
        "description_text": description_text,
        "description_html": description_html,  # structured Markdown text
        "adf_content": adf_content,  # original ADF content (if in ADF format)
        "image_attachments": image_attachments,  # list of image attachments
        "links": links,
        "linked_issues": linked_issues,
        "self_url": issue_data.get("self", ""),
    }

    if fetch_linked and base_url and auth_headers and linked_issues:
        keys = [item["key"] for item in linked_issues if item.get("key")]
        result["linked_issues_detail"] = fetch_linked_issue_details(
            base_url, auth_headers, keys
        )

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract requirement information from a Jira Issue")
    parser.add_argument("--url", required=True, help="Full URL of the Jira Issue")
    parser.add_argument("--output", "-o", help="Output file path (defaults to stdout)")
    parser.add_argument(
        "--with-linked",
        action="store_true",
        help="Additionally fetch the description and Confluence/Figma links of each Issue in linked_issues (one level)",
    )
    args = parser.parse_args()

    # Authentication - supports Cookie / Basic Auth (username/password) / Cloud API Token
    cookie = os.environ.get("JIRA_COOKIE")
    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")
    username = os.environ.get("JIRA_USERNAME")
    password = os.environ.get("JIRA_PASSWORD")
    domain_user = os.environ.get("JIRA_USERNAME")
    domain_pass = os.environ.get("JIRA_PASSWORD")
    if not (username and password) and not (domain_user and domain_pass) and not (email and api_token) and not cookie:
        print(
            "Please configure authentication (prefer the Windows system environment variables JIRA_USERNAME/PASSWORD or JIRA_USERNAME / JIRA_PASSWORD; config.local.env is an optional fallback):\n"
            "  Copy config.local.env.example -> config.local.env and fill it in",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse the URL and fetch the Issue
    base_url, issue_key = parse_jira_url(args.url)
    auth_headers = build_auth_headers()
    issue_data = fetch_issue(base_url, issue_key, auth_headers)
    result = process_issue(
        issue_data,
        fetch_linked=args.with_linked,
        base_url=base_url,
        auth_headers=auth_headers,
    )

    # Output
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Result written to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
