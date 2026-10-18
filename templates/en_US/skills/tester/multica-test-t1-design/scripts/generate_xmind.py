#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export test-case JSON to XMind 2020+ format (.xmind)
Compatible with XMind 2020 / XMind 8 / MindMaster / Baidu Naotu

Format notes (matches the test_cases_PROJ-123.xmind reference format):
  - Root topic title = project name (e.g. PLAT, PROJ)
  - Module topics end with / to denote folders
  - Multi-level module nesting is supported (module names separated by /)
  - Case structure: preconditions (first child node) + steps (expected results as child nodes)
  - Priority markers: P1->priority-1, P2->priority-2, P3->priority-3 (legacy P0->priority-1, P4->priority-3 also accepted)

  content.json: [
    {"id":"s1","class":"sheet","rootTopic":{"id":"root","title":"PLAT","children":{"attached":[...]}}}
  ]
  metadata.json: {"dataStructureVersion":"3","layoutEngineVersion":"5","creator":{...}}
  manifest.json: {"file-entries":{"content.json":{},"metadata.json":{}}}
"""
import json, os, sys, zipfile, uuid, re

# Fix Windows terminal encoding for non-ASCII output
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def _make_id():
    return uuid.uuid4().hex[:24]


def strip_module_prefix(name):
    """Strip ID prefix like 'FR-01 ' from module names, keep clean name"""
    return re.sub(r'^[A-Z]+-\d+\s+', '', name)


def build_topic_json(title, children=None, tid=None, markers=None):
    """Build the JSON dict of a single topic."""
    topic = {
        "id": tid or _make_id(),
        "title": title,
    }
    if children:
        topic["children"] = {"attached": children}
    if markers:
        topic["markers"] = markers
    return topic


def build_case_json(case_title, preconditions, steps, expected_results, priority):
    """Build the JSON structure of one test case.

    Format (matches test_cases_PROJ-123.xmind):
    {
      "id": "xxx",
      "title": "case title",
      "children": {
        "attached": [
          {"title": "Preconditions: xxx"},
          {
            "title": "steps",
            "children": {"attached": [
              {"title": "Expected: xxx"}
            ]}
          }
        ]
      },
      "markers": [{"markerId": "priority-1"}]
    }
    """
    children = []

    # Preconditions
    if preconditions:
        pc_text = "; ".join(p[:100] for p in preconditions)
        children.append(build_topic_json(f"Preconditions: {pc_text}"))

    # Strictly validate the number of expected results
    if len(steps) != len(expected_results):
        raise ValueError(
            f"Steps and expected results differ in count! case_title='{case_title}' "
            f"steps={len(steps)} expected_results={len(expected_results)}\n"
            f"Auto-filling expected results is forbidden; fix the generation logic and retry."
        )

    # Steps + expected results (one-to-one per step, output in full)
    # An expected result may use a multi-line numbered format: 1) xxx\n\n2) xxx\n\n3) xxx (still one expected result)
    for i, step in enumerate(steps):
        exp_text = expected_results[i]
        exp_list = [build_topic_json(f"Expected: {exp_text}")]
        step_node = build_topic_json(step, children=exp_list)
        children.append(step_node)

    # Priority mapping
    priority_map = {
        "P0": "priority-1",
        "P1": "priority-1",
        "P2": "priority-2",
        "P3": "priority-3",
        "P4": "priority-3",
    }
    marker_id = priority_map.get(priority, "priority-3")
    markers = [{"markerId": marker_id}]

    return build_topic_json(case_title, children=children, tid=_make_id(), markers=markers)


def build_module_tree(modules):
    """Convert a flat module list into a nested tree, supporting multi-level module paths.

    modules: [(mod_name, [case_tuple, ...]), ...]
      case_tuple = (title, preconditions, steps, expected, priority)
      mod_name may be "parent/child" to express nesting

    Returns: list of root-level topic JSONs (module names end with /)
    """
    tree = {}
    for mod_name, cases in modules:
        parts = [p.strip() for p in mod_name.split("/")]
        current = tree
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        leaf = parts[-1]
        if leaf not in current:
            current[leaf] = []
        current[leaf].extend(cases)

    def _serialize(subtree):
        topics = []
        for name, children in sorted(subtree.items()):
            if isinstance(children, list):
                case_list = [build_case_json(*c) for c in children]
                topics.append(build_topic_json(f"{name}/", children=case_list))
            else:
                child_topics = _serialize(children)
                topics.append(build_topic_json(f"{name}/", children=child_topics))
        return topics

    return _serialize(tree)


def build_sheet_json(sheet_title, root_title, module_topics):
    """Build the JSON of one Sheet.

    module_topics: topic list returned by build_module_tree
    """
    root_topic = build_topic_json(root_title, children=module_topics)
    return {
        "id": "s1",
        "class": "sheet",
        "rootTopic": root_topic,
    }


def group_by_module(test_cases):
    modules = {}
    for tc in test_cases:
        mod = tc.get("module", "Uncategorized")
        modules.setdefault(mod, []).append(tc)
    return sorted(modules.items(), key=lambda x: x[0])


def build_functional_sheets(data, project_key):
    """Build the functional-test Sheet."""
    func_cases = data.get("functional", [])
    if not func_cases:
        return None

    modules = group_by_module(func_cases)
    sheet_module_tuples = []
    for mod_name, cases in modules:
        module_cases = []
        clean_mod = strip_module_prefix(mod_name)  # "FR-01 File entry CRUD" -> "File entry CRUD"
        for c in cases:
            title = c.get("title", "")
            preconditions = c.get("preconditions", [])
            steps = c.get("steps", [])
            expected = c.get("expected_results", [])
            pri = c.get("priority", "")
            module_cases.append((title, preconditions, steps, expected, pri))
        sheet_module_tuples.append((clean_mod, module_cases))

    module_topics = build_module_tree(sheet_module_tuples)
    return build_sheet_json("Functional test cases", project_key, module_topics)


def build_api_sheets(data, project_key):
    """Build the API-test Sheet."""
    api_cases = data.get("api", [])
    if not api_cases:
        return None

    seen_apis = {}
    for tc in api_cases:
        name = tc.get("module", tc.get("api_name", "Uncategorized"))
        seen_apis.setdefault(name, []).append(tc)
    api_modules = sorted(seen_apis.items(), key=lambda x: x[0])

    sheet_module_tuples = []
    for mod_name, cases in api_modules:
        module_cases = []
        clean_mod = strip_module_prefix(mod_name)
        for c in cases:
            method = c.get("method", "")
            endpoint = c.get("api_endpoint", "")
            title = c.get("title", "")
            case_id = c.get("case_id", "")
            pri = c.get("priority", "P3")
            if endpoint:
                label = f"{case_id} [{method}] {endpoint} - {title}"
            else:
                label = f"{case_id} - {title}"
            steps = [f"Request parameter: {k}={v}" for k, v in c.get("request_params", {}).items()][:5]
            expected = c.get("validation_points", [])
            preconditions = c.get("preconditions", [])
            module_cases.append((label, preconditions, steps, expected, pri))
        sheet_module_tuples.append((clean_mod, module_cases))

    module_topics = build_module_tree(sheet_module_tuples)
    return build_sheet_json("API test cases", project_key, module_topics)


def extract_jira_key(data):
    """Extract the full requirement key (e.g. PROJ-100) from the case JSON."""
    if not isinstance(data, dict):
        return ""
    for field in ("jira_key", "parent_issue"):
        key = (data.get(field) or "").strip()
        if key and re.match(r'^[A-Z]+-\d+$', key):
            return key
        m = re.search(r'([A-Z]+-\d+)', key)
        if m:
            return m.group(1)
    return ""


def resolve_output_path(input_json, output_xmind, jira_key):
    """Resolve the output path: the file name must carry the requirement key; only the target file is written and no other .xmind is deleted.

    Naming convention: test_cases_{JIRA_KEY}.xmind(e.g. test_cases_PROJ-100.xmind)
    """
    input_dir = os.path.dirname(os.path.abspath(input_json)) or "."

    if not output_xmind:
        name = f"test_cases_{jira_key}.xmind" if jira_key else "test_cases.xmind"
        return os.path.join(input_dir, name)

    # If a directory is given, write into it named by the requirement key
    if os.path.isdir(output_xmind):
        name = f"test_cases_{jira_key}.xmind" if jira_key else "test_cases.xmind"
        return os.path.join(output_xmind, name)

    out_dir = os.path.dirname(os.path.abspath(output_xmind)) or input_dir
    base = os.path.basename(output_xmind)
    name, ext = os.path.splitext(base)
    if not ext:
        ext = ".xmind"

    # Append the requirement key when the file name lacks it, to avoid confusing overwrites of a fixed test_cases.xmind
    if jira_key and jira_key not in base:
        base = f"{name}_{jira_key}{ext}"
        return os.path.join(out_dir, base)

    return output_xmind


def generate(input_json, output_xmind=None, project_key=None):
    """Generate the XMind file.

    Args:
        input_json: Path of the test-case JSON file
        output_xmind: Output .xmind path; when None, auto-named by jira_key as
            test_cases_{JIRA_KEY}.xmind。Only the current target file is overwritten; old files of other requirements are not deleted.
        project_key: Project key (used as the root topic title). Defaults to None, in which case the prefix is extracted from jira_key in the data

    Returns:
        (success: bool, output_path: str|None)
    """
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict):
        test_cases = data
    else:
        test_cases = {"functional": [], "api": []}
        for tc in data:
            tc_type = tc.get("type", "")
            if tc_type == "api":
                test_cases.setdefault("api", []).append(tc)
            else:
                test_cases.setdefault("functional", []).append(tc)

    jira_key = extract_jira_key(test_cases)

    # Auto-extract the system prefix from jira_key as the root title (e.g. PROJ-100 -> PROJ)
    if project_key is None:
        if jira_key:
            m = re.match(r'([A-Z]+)-\d+', jira_key)
            project_key = m.group(1) if m else "PLAT"
        else:
            project_key = "PLAT"

    sheets = []
    func_sheet = build_functional_sheets(test_cases, project_key)
    if func_sheet:
        sheets.append(func_sheet)
    # API cases are not exported to XMind; they are only saved as a local JSON file
    if not sheets:
        print("Error: no test case data found", file=sys.stderr)
        return False, None

    output_path = resolve_output_path(input_json, output_xmind, jira_key)
    # Only write/overwrite the file for the current requirement; never delete other .xmind files in the directory
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    content_json = json.dumps(sheets, ensure_ascii=False, indent=2)

    metadata_json = json.dumps({
        "dataStructureVersion": "3",
        "layoutEngineVersion": "5",
        "creator": {
            "name": "TestCaseGenerator",
            "version": "1.0"
        }
    }, ensure_ascii=False, indent=2)

    manifest_json = json.dumps({
        "file-entries": {
            "content.json": {},
            "metadata.json": {}
        }
    }, ensure_ascii=False, indent=2)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('content.json', content_json.encode('utf-8'))
        zf.writestr('metadata.json', metadata_json.encode('utf-8'))
        zf.writestr('manifest.json', manifest_json.encode('utf-8'))

    return True, output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Export test cases to XMind 2020+ format (file name carries the requirement key; old files are not deleted)"
    )
    parser.add_argument("--input", "-i", required=True, help="Path of the test-case JSON file")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output .xmind path; if omitted, auto-named test_cases_{JIRA_KEY}.xmind. "
             "If test_cases.xmind is given and the JSON has jira_key, it is renamed to test_cases_{JIRA_KEY}.xmind",
    )
    parser.add_argument("--project", "-p", default=None, help="Project name/key (used as the root topic title; by default extracted from jira_key)")
    args = parser.parse_args()

    success, out_path = generate(args.input, args.output, project_key=args.project)
    if success and out_path:
        size = os.path.getsize(out_path)
        print(f"XMind generated: {out_path} ({size/1024:.1f} KB)")
        print("  Note: only the current requirement file was written; other .xmind files in the directory were not deleted")
        with zipfile.ZipFile(out_path, 'r') as zf:
            print(f"  Contains: {', '.join(zf.namelist())}")
    else:
        sys.exit(1)
