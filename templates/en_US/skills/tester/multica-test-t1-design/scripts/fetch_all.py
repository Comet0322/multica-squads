#!/usr/bin/env python3
"""
Test-data collection orchestrator: starting from Jira, automatically fetches Confluence requirement docs + Figma designs.

Usage:
  python scripts/fetch_all.py --jira-url https://your-domain.atlassian.net/browse/PROJ-123 --output-dir data/

Flow:
  1. multica-platform-jira get_issue.py -> extract Confluence/Figma links
  2. multica-platform-confluence fetch_page_by_url.py -> Markdown + JSON
  3. multica-platform-figma fetch_file.py -> design metadata
  4. aggregate JSON for case generation

Credentials: see the platform skills (JIRA_USERNAME / JIRA_PASSWORD / FIGMA_TOKEN); config.local.env is an optional fallback.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Fix Windows terminal encoding for non-ASCII output
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
_LIB = SKILL_DIR.parent.parent / "_lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from skill_resolver import resolve_skill_dir  # noqa: E402

try:
    import local_env  # noqa: F401  - loads config.local.env
except ImportError:
    pass


def platform_script(skill_name: str, script_name: str) -> Path:
    skill_dir = resolve_skill_dir(skill_name, SKILL_DIR)
    path = skill_dir / "scripts" / script_name
    if not path.is_file():
        raise FileNotFoundError(f"Platform script not found: {path}")
    return path


def run_script(script_path: Path, args: list[str]) -> str:
    """Run a platform script and return its stdout."""
    cmd = [sys.executable, str(script_path), *args]
    print(f"  -> Running: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if result.returncode != 0:
        print(f"  x Script {script_path.name} failed:\n{result.stderr}", file=sys.stderr)
        return ""
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description="Starting from Jira, automatically collect Confluence + Figma test data")
    parser.add_argument("--jira-url", required=True, help="Full URL of the Jira Issue")
    parser.add_argument("--output-dir", "-o", default="data", help="Output directory")
    parser.add_argument("--no-figma", action="store_true", help="Skip Figma collection")
    parser.add_argument("--no-confluence", action="store_true", help="Skip Confluence collection")
    parser.add_argument("--include-children", action="store_true", help="Include Confluence child pages")
    args = parser.parse_args()

    get_issue = platform_script("multica-platform-jira", "get_issue.py")
    fetch_conf = platform_script("multica-platform-confluence", "fetch_page_by_url.py")
    fetch_figma = platform_script("multica-platform-figma", "fetch_file.py")

    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Step 1: JIRA
    print("\n=== Step 1: Collect Jira Issue ===", file=sys.stderr)
    jira_output = os.path.join(output_dir, f"jira_issue_{timestamp}.json")
    run_script(get_issue, ["--url", args.jira_url, "--output", jira_output])
    if not os.path.exists(jira_output):
        print("x Jira collection failed, aborting", file=sys.stderr)
        sys.exit(1)
    print(f"OK Jira Issue saved: {jira_output}", file=sys.stderr)

    with open(jira_output, encoding="utf-8") as f:
        jira_data = json.load(f)

    print(f"  Title: {jira_data.get('summary', '')}", file=sys.stderr)
    print(f"  Confluence links: {len(jira_data['links']['confluence_links'])}", file=sys.stderr)
    print(f"  Figma links: {len(jira_data['links']['figma_links'])}", file=sys.stderr)

    # Step 2: Confluence
    confluence_results = []
    if not args.no_confluence:
        print("\n=== Step 2: Collect Confluence requirement docs ===", file=sys.stderr)
        for i, link in enumerate(jira_data["links"]["confluence_links"], 1):
            print(f"  [{i}/{len(jira_data['links']['confluence_links'])}] {link}", file=sys.stderr)
            md_output = os.path.join(output_dir, f"confluence_page_{i}_{timestamp}.md")
            json_output = os.path.join(output_dir, f"confluence_page_{i}_{timestamp}.json")
            image_dir = os.path.join(output_dir, f"confluence_images_{i}_{timestamp}")
            script_args = [
                "--url",
                link,
                "--output",
                md_output,
                "--json",
                json_output,
                "--image-dir",
                image_dir,
            ]
            if args.include_children:
                script_args.append("--include-children")

            run_script(fetch_conf, script_args)

            if os.path.exists(md_output):
                print(f"  OK Saved: {md_output}", file=sys.stderr)
                confluence_results.append(
                    {
                        "url": link,
                        "markdown": md_output,
                        "json": json_output,
                        "image_dir": image_dir,
                    }
                )
            else:
                print(f"  x Collection failed: {link}", file=sys.stderr)

    # Step 3: Figma
    figma_results = []
    if not args.no_figma:
        print("\n=== Step 3: Collect Figma designs ===", file=sys.stderr)
        for i, link in enumerate(jira_data["links"]["figma_links"], 1):
            print(f"  [{i}/{len(jira_data['links']['figma_links'])}] {link}", file=sys.stderr)
            json_output = os.path.join(output_dir, f"figma_file_{i}_{timestamp}.json")
            summary_output = os.path.join(output_dir, f"figma_file_{i}_{timestamp}_summary.txt")

            run_script(
                fetch_figma,
                ["--url", link, "--output", json_output, "--summary", summary_output],
            )

            if os.path.exists(json_output):
                print(f"  OK Saved: {json_output}", file=sys.stderr)
                figma_results.append(
                    {
                        "url": link,
                        "json": json_output,
                        "summary": summary_output,
                    }
                )
            else:
                print(f"  x Collection failed: {link}", file=sys.stderr)

    # Step 4: Aggregate
    print("\n=== Step 4: Summary ===", file=sys.stderr)

    has_rich_content = False
    total_images = 0
    confluence_details = []

    for cr in confluence_results:
        detail = {"url": cr["url"], "title": "", "has_rich_content": False, "image_count": 0}
        if os.path.exists(cr.get("json", "")):
            try:
                with open(cr["json"], encoding="utf-8") as f:
                    cdata = json.load(f)
                detail["title"] = cdata.get("title", "")
                rich = cdata.get("has_rich_content", {})
                if isinstance(rich, dict):
                    detail["has_rich_content"] = any(rich.values())
                    detail["has_tables"] = rich.get("has_tables", False)
                    detail["has_lists"] = rich.get("has_lists", False)
                    detail["has_images"] = rich.get("has_images", False)
                    downloaded = cdata.get("downloaded_images") or []
                    ok_imgs = [d for d in downloaded if d.get("status") == "ok"]
                    detail["image_count"] = len(ok_imgs) or len(cdata.get("image_references", []))
                    detail["image_dir"] = cdata.get("image_dir") or cr.get("image_dir")
                if detail["has_rich_content"]:
                    has_rich_content = True
                    total_images += detail["image_count"]
            except Exception:
                pass
        confluence_details.append(detail)

    summary = {
        "jira": {
            "url": args.jira_url,
            "key": jira_data.get("key", ""),
            "summary": jira_data.get("summary", ""),
            "data_file": jira_output,
            "description_text": jira_data.get("description_text", ""),
            "description_html": jira_data.get("description_html", ""),
            "image_attachments": jira_data.get("image_attachments", []),
        },
        "confluence_pages": confluence_results,
        "confluence_details": confluence_details,
        "figma_files": figma_results,
        "total": {
            "jira_issues": 1,
            "confluence_pages": len(confluence_results),
            "figma_files": len(figma_results),
        },
        "rich_content": {
            "has_rich_content": has_rich_content,
            "total_images": total_images,
            "has_confluence_html_tables": any(d.get("has_tables", False) for d in confluence_details),
            "has_confluence_html_lists": any(d.get("has_lists", False) for d in confluence_details),
            "has_confluence_images": any(d.get("has_images", False) for d in confluence_details),
            "has_jira_images": len(jira_data.get("image_attachments", [])) > 0,
        },
    }

    summary_file = os.path.join(output_dir, f"summary_{timestamp}.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nOK All done! Output directory: {output_dir}", file=sys.stderr)
    print(f"  - Summary file: {summary_file}", file=sys.stderr)
    print(f"  - Jira: {jira_data.get('key', '')}", file=sys.stderr)
    print(f"  - Confluence: {len(confluence_results)} pages", file=sys.stderr)
    print(f"  - Figma: {len(figma_results)} files", file=sys.stderr)

    if total_images > 0:
        print(
            f"\nWARNING: found {total_images} Confluence image references; read the image contents with the Read tool",
            file=sys.stderr,
        )
    if jira_data.get("image_attachments"):
        print(
            f"WARNING: found {len(jira_data['image_attachments'])} Jira image attachments; "
            "download them and read the image contents with the Read tool",
            file=sys.stderr,
        )
    if has_rich_content:
        print("WARNING: Confluence pages contain HTML rich-text structure (tables/lists); structured information has been preserved", file=sys.stderr)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
