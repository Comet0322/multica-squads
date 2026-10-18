#!/usr/bin/env python3
"""
Figma file reader (platform) — structured design metadata + text summary.

Usage:
  python scripts/fetch_file.py --url https://www.figma.com/file/ABC123/design?node-id=0-1
  python scripts/fetch_file.py --url https://www.figma.com/design/ABC123/design --output data/figma_design.json

Environment variables:
  FIGMA_TOKEN  - Figma Personal Access Token(get it from Figma > Settings > Account > Personal Access Tokens)

Output:
  - Design info as JSON (metadata for pages, frames, components, layers, styles, etc.)
  - Text summary (directly readable by Claude)
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

from urllib.parse import urlparse, parse_qs
from html import unescape

try:
    import local_env  # noqa: F401  — loads config.local.env
except ImportError:
    pass

try:
    import requests
except ImportError:
    print('Missing requests library; run: pip install requests', file=sys.stderr)
    sys.exit(1)


# ============================================================
# Figma API
# ============================================================

FIGMA_API_BASE = "https://api.figma.com/v1"


def build_headers() -> dict:
    token = os.environ.get("FIGMA_TOKEN", "")
    if not token:
        print(
            "Please configure FIGMA_TOKEN (recommended: put it in config.local.env in the skill directory)\n"
            "  Generate one at Figma > Settings > Account > Personal Access Tokens",
            file=sys.stderr,
        )
        sys.exit(1)
    return {"X-Figma-Token": token}


def parse_figma_url(url: str) -> tuple[str, str | None]:
    """
    Parse file_key and node_id from a Figma URL.
    URL formats:
      - https://www.figma.com/file/ABC123/design-name
      - https://www.figma.com/file/ABC123/design-name?node-id=0-1
      - https://www.figma.com/design/ABC123/design-name
      - https://www.figma.com/proto/ABC123/design-name
    """
    parsed = urlparse(url)

    # Extract file_key: /file/KEY, /design/KEY or /proto/KEY
    m = re.search(r'/(?:file|design|proto)/([a-zA-Z0-9]+)', parsed.path)
    if not m:
        raise ValueError(f"Cannot parse File Key from URL: {url}")
    file_key = m.group(1)

    # Extract node-id
    params = parse_qs(parsed.query)
    node_id = params.get("node-id", [None])[0]

    return file_key, node_id


def fetch_file_info(file_key: str, headers: dict) -> dict:
    """Fetch Figma file metadata"""
    url = f"{FIGMA_API_BASE}/files/{file_key}"
    resp = requests.get(url, headers=headers, timeout=60)
    if resp.status_code == 403:
        print("Authentication failed: check that FIGMA_TOKEN has access to this file", file=sys.stderr)
        sys.exit(1)
    if resp.status_code == 404:
        print(f"Figma file not found: {file_key}", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


def fetch_file_nodes(file_key: str, node_ids: list[str], headers: dict) -> dict:
    """Fetch detailed info for the given nodes"""
    ids = ",".join(node_ids)
    url = f"{FIGMA_API_BASE}/files/{file_key}/nodes?ids={ids}"
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def fetch_file_images(file_key: str, node_ids: list[str], headers: dict) -> dict:
    """Fetch image export links for nodes"""
    ids = ",".join(node_ids)
    url = f"{FIGMA_API_BASE}/images/{file_key}?ids={ids}&format=png&scale=1"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ============================================================
# Design element extraction
# ============================================================

def extract_node_info(node: dict, depth: int = 0) -> dict | None:
    """Recursively extract key node info"""
    if not isinstance(node, dict):
        return None

    node_type = node.get("type", "")
    node_name = node.get("name", "")

    # Skip overly low-level geometry nodes; focus on meaningful design elements
    if node_type in ("VECTOR", "LINE", "ELLIPSE", "POLYGON", "STAR") and depth > 3:
        return None

    info = {
        "id": node.get("id", ""),
        "name": node_name,
        "type": node_type,
        "visible": node.get("visible", True),
    }

    # Extract constraint info
    constraints = node.get("constraints", {})
    if constraints:
        info["constraints"] = constraints

    # Extract relative position info
    bbox = node.get("absoluteBoundingBox", {})
    if bbox:
        info["position"] = {
            "x": round(bbox.get("x", 0), 1),
            "y": round(bbox.get("y", 0), 1),
        }
        info["size"] = {
            "width": round(bbox.get("width", 0), 1),
            "height": round(bbox.get("height", 0), 1),
        }

    # Fill color (background)
    fills = node.get("fills", [])
    if fills and isinstance(fills, list):
        solid_fills = [f for f in fills if f.get("type") == "SOLID" and f.get("visible", True)]
        if solid_fills:
            color = solid_fills[0].get("color", {})
            info["background_color"] = {
                "r": round(color.get("r", 0) * 255),
                "g": round(color.get("g", 0) * 255),
                "b": round(color.get("b", 0) * 255),
                "a": round(color.get("a", 1), 2),
            }

    # Text content
    if node_type == "TEXT":
        info["text"] = node.get("characters", "")
        style = node.get("style", {})
        if style:
            info["text_style"] = {
                "font_family": style.get("fontFamily", ""),
                "font_size": style.get("fontSize", ""),
                "font_weight": style.get("fontWeight", ""),
                "text_align": style.get("textAlignHorizontal", ""),
                "line_height": style.get("lineHeightPx", ""),
            }

    # Component/instance references
    if node_type == "COMPONENT":
        info["component_property_definitions"] = node.get("componentPropertyDefinitions", {})

    if node_type == "INSTANCE":
        info["main_component"] = node.get("mainComponent", {})

    # Interaction settings
    interactions = node.get("interactions", [])
    if interactions:
        info["interactions"] = [
            {
                "trigger": i.get("trigger", {}).get("type", ""),
                "action": i.get("action", {}).get("type", ""),
                "destination": i.get("action", {}).get("destinationId", ""),
            }
            for i in interactions if isinstance(i, dict)
        ]

    return info


def traverse_canvases(document: dict) -> list[dict]:
    """Walk all Canvases (pages) and Frames of the document"""
    canvases = []
    children = document.get("children", [])
    for child in children:
        if child.get("type") in ("CANVAS", "FRAME", "GROUP"):
            canvas_info = extract_node_info(child)
            if canvas_info:
                frames = []
                for frame_node in child.get("children", []):
                    frame_info = extract_node_info(frame_node)
                    if frame_info:
                        sub_elements = _collect_visible_elements(frame_node)
                        frame_info["elements"] = sub_elements
                        frames.append(frame_info)
                canvas_info["frames"] = frames
                canvases.append(canvas_info)
    return canvases


def _collect_visible_elements(node: dict, depth: int = 0, max_depth: int = 5) -> list[dict]:
    """Recursively collect visible child elements"""
    if depth > max_depth:
        return []
    elements = []
    for child in node.get("children", []):
        info = extract_node_info(child, depth)
        if info and info.get("visible", True):
            # Keep recursing to collect deeper elements
            sub_elements = _collect_visible_elements(child, depth + 1, max_depth)
            if sub_elements:
                info["children"] = sub_elements
            elements.append(info)
    return elements


def extract_components(document: dict) -> list[dict]:
    """Extract all components in the document (COMPONENT and COMPONENT_SET)"""
    components = []

    def _walk(node):
        if not isinstance(node, dict):
            return
        node_type = node.get("type", "")
        if node_type in ("COMPONENT", "COMPONENT_SET"):
            components.append(extract_node_info(node))
        for child in node.get("children", []):
            _walk(child)

    _walk(document)
    return components


def extract_styles(file_data: dict) -> list[dict]:
    """Extract style definitions in the file"""
    styles = file_data.get("styles", {})
    result = []
    for style_id, style_info in styles.items():
        result.append({
            "style_id": style_id,
            "name": style_info.get("name", ""),
            "type": style_info.get("styleType", ""),
            "description": style_info.get("description", ""),
        })
    return result


# ============================================================
# Main flow
# ============================================================

def build_design_summary(file_info: dict, canvases: list[dict], components: list[dict]) -> dict:
    """Build the design summary (structured summary for Claude to read)"""
    name = file_info.get("name", "")
    pages = []
    for canvas in canvases:
        page_info = {
            "page_name": canvas.get("name", ""),
            "page_type": canvas.get("type", ""),
            "frames": [],
        }
        for frame in canvas.get("frames", []):
            frame_info = {
                "frame_name": frame.get("name", ""),
                "size": frame.get("size", {}),
                "elements": [],
            }
            for elem in frame.get("elements", []):
                frame_info["elements"].append({
                    "name": elem.get("name", ""),
                    "type": elem.get("type", ""),
                    "text": elem.get("text", "") if elem.get("type") == "TEXT" else None,
                    "size": elem.get("size", {}),
                    "position": elem.get("position", {}),
                    "children_count": len(elem.get("children", [])),
                })
            page_info["frames"].append(frame_info)
        pages.append(page_info)

    return {
        "file_name": name,
        "pages": pages,
        "total_components": len(components),
        "component_names": [c.get("name", "") for c in components if c],
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch UI design info from Figma")
    parser.add_argument("--url", required=True, help="full URL of the Figma file")
    parser.add_argument("--output", "-o", help="output JSON file path")
    parser.add_argument("--summary", "-s", help="output text summary file path (directly readable by Claude)")
    args = parser.parse_args()

    headers = build_headers()
    file_key, node_id = parse_figma_url(args.url)

    # Fetch file info
    print(f"Fetching Figma file: {file_key} ...", file=sys.stderr)
    file_data = fetch_file_info(file_key, headers)
    document = file_data.get("document", {})

    # Extract structured info
    canvases = traverse_canvases(document)
    components = extract_components(document)
    styles = extract_styles(file_data)

    # Build summary
    summary = build_design_summary(file_data, canvases, components)

    # Build full output
    result = {
        "file_name": file_data.get("name", ""),
        "last_modified": file_data.get("lastModified", ""),
        "version": file_data.get("version", ""),
        "thumbnail_url": file_data.get("thumbnailUrl", ""),
        "canvases": canvases,
        "components": components,
        "styles": styles,
        "design_summary": summary,
    }

    # Output
    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"JSON written to: {args.output}", file=sys.stderr)

    if args.summary:
        os.makedirs(os.path.dirname(args.summary) or ".", exist_ok=True)
        with open(args.summary, "w", encoding="utf-8") as f:
            f.write(f"# Figma design summary: {summary['file_name']}\n\n")
            f.write(f"Pages: {len(summary['pages'])}\n")
            f.write(f"Components: {summary['total_components']}\n")
            f.write(f"Component list: {', '.join(summary['component_names'])}\n\n")
            for page in summary['pages']:
                f.write(f"## {page['page_name']}\n")
                for frame in page['frames']:
                    size = frame.get('size', {})
                    f.write(f"  - {frame['frame_name']} ({size.get('width', '?')}×{size.get('height', '?')}): {len(frame['elements'])} visible elements\n")
                    for elem in frame['elements']:
                        text = f" → \"{elem['text'][:50]}\"" if elem.get('text') else ""
                        f.write(f"    - [{elem['type']}] {elem['name']}{text}\n")
            f.write("\n")
        print(f"Summary written to: {args.summary}", file=sys.stderr)

    if not args.output and not args.summary:
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
