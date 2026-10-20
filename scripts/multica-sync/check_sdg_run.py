#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check one software-development-gateway run against its acceptance criteria.

Reads the issue, its timeline and task runs from Multica, the backend log,
the git gateway audit log and the repo branches, then prints one line per
criterion (PASS / FAIL / SKIP C<n>) and `ALL PASS` or `SOME FAIL`.

  C1  issue ends in_review; the Leader gets a task within 60s of every member comment
  C2  every member comment was posted by the agent itself (not the completion fallback)
  C3  every dispatch carries the artifact's Expected template verbatim
  C4  every delivery matches its template (lines, no Markdown, 40-hex Commit, Summary <= 3 lines)
  C5  a malformed delivery goes back to its producer, not to review
  C6  one review skill per review dispatch; review lines match the REVIEW template
  C7  a FAIL goes back to the same producer; at most 3 review rounds per artifact
  C8  order: PRD -> DESIGN -> (UI) -> BACKEND (+ FRONTEND in parallel) -> TEST
  C9  the gateway rejected no push; no comment mentions raw git / `multica repo checkout`
  C10 every push came from the role that owns the branch, after a git_clone
  C11 the spec branch only holds the PRD / design / UI files
  C12 exactly one MR from demo/<KEY>, and its Test command passes when run here
  C13 the final Gate lists the MR, commits and open items
  C14 every document's headings match its template in sdg-review-<type>
  C15 an issue filed from the PM chat (`Spec chat:`) keeps its sections, AC ids and scope in the repo PRD
  C16 in that chat the PM pasted an all-PASS self-check before the human said to create it

Usage (Python 3.9+, stdlib only; host/token/workspace come from env or config.local.json):

  export MULTICA_API_TOKEN=mul_xxx MULTICA_API_URL=https://multica.example.com
  python check_sdg_run.py <issue-id-or-key> --workspace <slug> --ui yes \\
      --repo-url <clone URL of the product repo> \\
      --backend-container <multica backend container> --gateway-container <gateway container>

C2 needs --backend-container and C9/C10 need --gateway-container (both read via
`docker`); without them those criteria print SKIP. --path-prefix puts a
directory (e.g. a venv's bin) first on PATH when running the Test command.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from multica_client import MulticaClient, MulticaError, load_local_config, utf8_stdio
from repo_paths import resolve_template_file, skills_dir

HERE = Path(__file__).resolve().parent
PRODUCER = {"PRD": "sdg-pm", "DESIGN": "sdg-architect", "UI": "sdg-designer",
            "BACKEND": "sdg-backend", "FRONTEND": "sdg-frontend", "TEST": "sdg-tester"}


def as_list(data, *keys) -> list:
    if isinstance(data, list):
        return data
    for k in keys:
        if isinstance(data, dict) and isinstance(data.get(k), list):
            return data[k]
    return []


def ts(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    if re.search(r"[+-]\d{4}$", s):
        s = s[:-2] + ":" + s[-2:]
    return datetime.fromisoformat(s)


def main() -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(description="Check one software-development-gateway run")
    ap.add_argument("issue", help="issue UUID or key (e.g. ABC-12)")
    ap.add_argument("--workspace", default="", help="workspace slug (or MULTICA_WORKSPACE / config.local.json)")
    ap.add_argument("--url", default=None, help="Multica base URL (or MULTICA_API_URL)")
    ap.add_argument("--config", default=str(HERE / "software-development-gateway.json"), help="bootstrap config")
    ap.add_argument("--ui", choices=["yes", "no"], required=True, help="does this task have a user interface")
    ap.add_argument("--repo-url", required=True, help="clone URL of the product repo (read access)")
    ap.add_argument("--backend-container", default="", help="docker container of the Multica backend (for C2)")
    ap.add_argument("--gateway-container", default="", help="docker container of the git gateway (for C9/C10)")
    ap.add_argument("--audit-log", default="/var/lib/gw/audit.log", help="audit log path inside the gateway container")
    ap.add_argument("--chat-session", default="", help="chat session id the issue was filed from (for C16)")
    ap.add_argument("--path-prefix", default="", help="directory put first on PATH when running the Test command")
    args = ap.parse_args()

    workspace = args.workspace or os.environ.get("MULTICA_WORKSPACE") or str(load_local_config().get("workspace") or "")
    if not workspace:
        print("Missing workspace: pass --workspace or set MULTICA_WORKSPACE", file=sys.stderr)
        return 2
    client = MulticaClient.from_env(args.url)

    def get(path):
        data, _ = client._request("GET", path, workspace=workspace)
        return data

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    stem_name = {a["stem"]: a.get("name") or a["stem"] for a in config["agents"]}
    agents = {a["id"]: a["name"] for a in as_list(get("/api/agents"), "agents") if a["name"] in stem_name.values()}
    role = {v: k for k, v in agents.items()}
    name = stem_name.get

    issue = get(f"/api/issues/{args.issue}")
    issue_id, key = issue["id"], issue["identifier"]
    timeline = as_list(get(f"/api/issues/{issue_id}/timeline"), "entries", "timeline")
    tasks = as_list(get(f"/api/issues/{issue_id}/task-runs"), "tasks", "runs")
    comments = [c for c in timeline if c.get("type") == "comment"]
    for c in comments:
        c["who"] = agents.get(c.get("actor_id"), c.get("actor_type"))
        c["content"] = c.get("content") or ""
    leader, reviewer = name("sdg-leader"), name("sdg-reviewer")
    producers = {art: name(stem) for art, stem in PRODUCER.items()}
    results = []

    def res(n, ok, detail=""):
        results.append((n, ok, detail))

    # Templates from the squad instructions
    squad_text = resolve_template_file(config["squad"]["instructions_file"]).read_text(encoding="utf-8")
    block = squad_text.split("```text\n", 1)[1]

    def template(t):
        m = re.search(rf"^{t}:\n((?:.+\n)+?)\n", block, re.M)
        return m.group(1).splitlines() if m else []

    base = {t: template(t) for t in ("PRD", "BACKEND", "TEST")}

    def expand(t):
        if t in base:
            return base[t]
        src = "PRD" if t in ("DESIGN", "UI") else "BACKEND"
        out = []
        for line in base[src]:
            if line.startswith("Artifact:"):
                line = f"Artifact: {t}"
            elif line.startswith("Path:") and t == "DESIGN":
                line = "Path: docs/design/<ISSUE-KEY>/design.md"
            elif line.startswith("Path:") and t == "UI":
                line = "Path: docs/design/<ISSUE-KEY>/ui.md"
            elif line.startswith("Branch:") and t == "FRONTEND":
                line = "Branch: demo/<ISSUE-KEY>-frontend"
            out.append(line)
        return out

    deliveries = [c for c in comments if c["who"] in producers.values() and not c["content"].startswith("**Blocked")]
    reviews = [c for c in comments if c["who"] == reviewer]
    leader_c = [c for c in comments if c["who"] == leader]

    def artifact_of(c):
        m = re.search(r"^Artifact:\s*(\w+)", c["content"], re.M)
        return m.group(1) if m else {v: k for k, v in producers.items()}.get(c["who"])

    # C1
    lead_tasks = [t for t in tasks if t["agent_id"] == role.get(leader)]
    missing = []
    for c in comments:
        if c["who"] == leader or c.get("actor_type") != "agent":
            continue
        t0 = ts(c["created_at"])
        if not any(t0 - timedelta(seconds=5) <= ts(t["created_at"]) <= t0 + timedelta(seconds=60) for t in lead_tasks):
            missing.append(f"{c['who']}@{c['created_at'][11:19]}")
    res(1, issue["status"] == "in_review" and not missing, f"status={issue['status']} leader-not-woken={missing}")

    # C2
    if args.backend_container:
        since = min(c["created_at"] for c in comments)
        log = subprocess.run(["docker", "logs", args.backend_container, "--since", since], capture_output=True, text=True)
        created = set(re.findall(r"comment created .*?comment_id=(\S+)", log.stdout + log.stderr))
        fallback = [f"{c['who']}@{c['created_at'][11:19]}" for c in comments if c.get("actor_type") == "agent" and c["id"] not in created]
        res(2, not fallback, f"fallback-posted={fallback}")
    else:
        res(2, None, "no --backend-container")

    # C3 / C4 / C5
    c3, c4, c5 = [], [], []
    for d in deliveries:
        art = artifact_of(d)
        exp = [line.replace("<ISSUE-KEY>", key) for line in expand(art)]
        disp = [c for c in leader_c if role[d["who"]] in c["content"] and c["created_at"] <= d["created_at"]]
        if not disp or not all(line in disp[-1]["content"] for line in exp):
            c3.append(f"{art}@{d['created_at'][11:19]}")
        keys = [line.split(":", 1)[0] for line in exp]
        got = [line.split(":", 1)[0] for line in d["content"].splitlines() if re.match(r"^[A-Za-z ]+:", line)]
        seen = [k for k in got if k in keys]
        seen = [k for i, k in enumerate(seen) if i == 0 or k != seen[i - 1]]
        problems = []
        if "**" in d["content"] or re.search(r"^#", d["content"], re.M):
            problems.append("markdown")
        if seen != keys:
            problems.append("lines")
        m = re.search(r"^Commit:\s*([0-9a-f]+)\s*$", d["content"], re.M)
        if not m or len(m.group(1)) != 40:
            problems.append("commit")
        if len(re.findall(r"^Summary:", d["content"], re.M)) > 3:
            problems.append("summary>3")
        if problems:
            c4.append(f"{art}@{d['created_at'][11:19]}:{','.join(problems)}")
            nxt = [c for c in leader_c if c["created_at"] > d["created_at"]]
            if not nxt or role[reviewer] in nxt[0]["content"] or role[d["who"]] not in nxt[0]["content"]:
                c5.append(f"{art}@{d['created_at'][11:19]}")
    res(3, not c3, f"dispatch-without-verbatim-template={c3}")
    res(4, not c4 or not c5, f"bad-deliveries={c4} (fine when every one was sent back, see C5)")
    res(5, not c5, f"bad-delivery-not-sent-back={c5}")

    # C6 / C7
    c6, c7, rounds = [], [], {}
    for c in leader_c:
        if role[reviewer] in c["content"] and len(set(re.findall(r"sdg-review-\w+", c["content"]))) != 1:
            c6.append(f"skills@{c['created_at'][11:19]}")
    for r in reviews:
        first = r["content"].strip().splitlines()[0]
        m = re.match(r"^REVIEW (PRD|DESIGN|UI|BACKEND|FRONTEND|TEST) demo/\S+@[0-9a-f]{40}: (PASS|FAIL)$", first)
        if not m:
            c6.append(f"bad-review-line@{r['created_at'][11:19]}")
            continue
        art = m.group(1)
        rounds[art] = rounds.get(art, 0) + 1
        if m.group(2) == "FAIL":
            nxt = [c for c in leader_c if c["created_at"] > r["created_at"] and any(role[p] in c["content"] for p in producers.values())]
            if not nxt or role[producers[art]] not in nxt[0]["content"]:
                c7.append(f"{art}-FAIL@{r['created_at'][11:19]}")
    c7 += [f"{k}:{n}rounds" for k, n in rounds.items() if n > 3]
    res(6, not c6, str(c6))
    res(7, not c7, f"{c7} rounds={rounds}")

    # C8
    ui = args.ui == "yes"
    passes, first_disp = {}, {}
    for r in reviews:
        first = r["content"].strip().splitlines()[0]
        if first.endswith("PASS") and len(first.split()) > 1:
            passes.setdefault(first.split()[1], r["created_at"])
    for c in leader_c:
        for art, who in producers.items():
            if role[who] in c["content"]:
                first_disp.setdefault(art, c["created_at"])

    def before(a, b):
        return a in passes and b in first_disp and passes[a] <= first_disp[b]

    seq = ["PRD", "DESIGN"] + (["UI"] if ui else []) + ["BACKEND"] + (["FRONTEND"] if ui else []) + ["TEST"]
    ok8 = all(a in passes for a in seq) and before("PRD", "DESIGN") and before("BACKEND", "TEST")
    if ui:
        ok8 = ok8 and before("DESIGN", "UI") and before("UI", "BACKEND") and before("UI", "FRONTEND") and before("FRONTEND", "TEST")
        ok8 = ok8 and abs((ts(first_disp["BACKEND"]) - ts(first_disp["FRONTEND"])).total_seconds()) < 120
    else:
        ok8 = ok8 and "UI" not in first_disp and "FRONTEND" not in first_disp and before("DESIGN", "BACKEND")
    res(8, ok8, f"passes={sorted(passes)} dispatched={sorted(first_disp)}")

    # C9 / C10
    ev = []
    if args.gateway_container:
        audit = subprocess.run(["docker", "exec", args.gateway_container, "cat", args.audit_log], capture_output=True, text=True).stdout
        ev = [json.loads(line) for line in audit.splitlines() if line.strip()]
        mine = [e for e in ev if key.lower() + "-" in (e.get("dest") or "") or (e.get("branch") or "").startswith(f"demo/{key}")]
        bad_push = [f"{e['branch']}:{e.get('error', '')[:60]}" for e in mine if e["event"] == "push" and not e.get("ok")]
        raw_git = [f"{c['who']}@{c['created_at'][11:19]}" for c in comments if re.search(r"multica repo checkout|git push origin", c["content"])]
        res(9, not bad_push and not raw_git, f"rejected-pushes={bad_push} raw-git-mentions={raw_git}")
        owner = {f"demo/{key}-spec": {producers["PRD"], producers["DESIGN"], producers["UI"]},
                 f"demo/{key}-backend": {producers["BACKEND"]}, f"demo/{key}-frontend": {producers["FRONTEND"]},
                 f"demo/{key}": {producers["TEST"]}}
        wrong = []
        for e in mine:
            if e["event"] != "push" or not e.get("ok"):
                continue
            t = ts(e["ts"])
            running = {agents.get(x["agent_id"]) for x in tasks if x.get("started_at") and ts(x["started_at"]) <= t
                       and (not x.get("completed_at") or t <= ts(x["completed_at"]))}
            if not running & owner.get(e["branch"], set()):
                wrong.append(f"{e['branch']}@{e['ts'][11:19]} running={sorted(n for n in running if n)}")
            if not any(c["event"] == "clone" and c.get("ok") and ts(c["ts"]) <= t for c in mine):
                wrong.append(f"{e['branch']}@{e['ts'][11:19]} no-prior-clone")
        res(10, not wrong, str(wrong))
    else:
        res(9, None, "no --gateway-container")
        res(10, None, "no --gateway-container")

    # C11 / C12 / C14
    tmp = tempfile.mkdtemp()
    subprocess.run(["git", "clone", "-q", args.repo_url, tmp], check=True)

    def git(*a):
        return subprocess.run(["git", "-C", tmp, *a], capture_output=True, text=True).stdout

    spec_files = git("diff", "--name-only", f"origin/main...origin/demo/{key}-spec").split()
    allowed = {f"docs/prd/{key}.md", f"docs/design/{key}/design.md", f"docs/design/{key}/ui.md"}
    res(11, bool(spec_files) and set(spec_files) <= allowed, f"spec-branch-files={spec_files}")

    test_d = next((d for d in reversed(deliveries) if artifact_of(d) == "TEST"), None)
    m = re.search(r"^Test command:\s*(.+)$", test_d["content"], re.M) if test_d else None
    cmd = m.group(1).strip() if m else ""
    env = dict(os.environ)
    if args.path_prefix:
        env["PATH"] = args.path_prefix + os.pathsep + env["PATH"]
    run = subprocess.run(f"git checkout -q origin/demo/{key} && {cmd}", shell=True, cwd=tmp, capture_output=True,
                         text=True, timeout=900, env=env) if cmd else None
    mrs = [e for e in ev if e["event"] == "open_mr" and (e.get("branch") or "").startswith(f"demo/{key}")]
    final = leader_c[-1]["content"] if leader_c else ""
    mr_links = re.findall(r"merge_requests/\d+", final)
    mr_ok = (len(mrs) == 1 and mrs[0]["branch"] == f"demo/{key}" and mrs[0].get("ok")) if args.gateway_container else len(set(mr_links)) == 1
    ok12 = mr_ok and run is not None and run.returncode == 0
    tail = (run.stdout + run.stderr)[-200:] if run and run.returncode else ""
    res(12, ok12, f"mrs={[e['branch'] for e in mrs] or mr_links} test rc={run.returncode if run else None} cmd={cmd!r} {tail}")

    shas = set(re.findall(r"[0-9a-f]{40}", final))
    ok13 = bool(mr_links) and len(shas) >= len(passes) and bool(re.search(r"\b(open|unresolved)\b", final, re.I))
    res(13, ok13, f"mr={mr_links} commits={len(shas)} artifacts={len(passes)} " + final[:120].replace("\n", " "))

    c14 = []
    for kind, path in (("prd", f"docs/prd/{key}.md"), ("design", f"docs/design/{key}/design.md"), ("ui", f"docs/design/{key}/ui.md")):
        if kind == "ui" and not ui:
            continue
        skill = next(skills_dir().rglob(f"sdg-review-{kind}/SKILL.md"))
        tpl = skill.read_text(encoding="utf-8").split("```markdown", 1)[1].split("```", 1)[0]
        want = re.findall(r"^#{1,2} .+$", tpl.replace("<ISSUE-KEY>", key), re.M)
        got = re.findall(r"^#{1,2} .+$", git("show", f"origin/demo/{key}-spec:{path}"), re.M)
        if got != want:
            c14.append(f"{kind}: want={want} got={got}")
    res(14, not c14, str(c14))

    # C15: a chat-confirmed spec keeps its meaning in the repo (same sections, same AC ids, same scope bullets count)
    desc = issue.get("description") or ""
    if desc.startswith("Spec chat:"):
        prd = git("show", f"origin/demo/{key}-spec:docs/prd/{key}.md")

        def shape(text):
            heads = re.findall(r"^## .+$", text, re.M)
            acs = re.findall(r"^- (AC-\d+):", text, re.M)
            scope = text.split("## Scope", 1)[-1].split("\n## ", 1)[0]
            return heads, acs, len(re.findall(r"^- ", scope, re.M))
        res(15, shape(desc) == shape(prd), f"issue={shape(desc)} prd={shape(prd)}")
    else:
        res(15, None, "not a chat spec")

    # C16: in the chat, the PM pasted a full PASS self-check before the human said to create the issue
    if args.chat_session:
        msgs, _ = client._request("GET", f"/api/chat/sessions/{args.chat_session}/messages", workspace=workspace)
        msgs = as_list(msgs, "messages")
        go = next((i for i, m in enumerate(msgs) if m.get("role") == "user" and re.search(r"create it", m.get("content") or "", re.I)), None)
        prev = next((m for m in reversed(msgs[:go]) if m.get("role") == "assistant"), None) if go is not None else None
        checks = re.findall(r"Self-check (\d+): (PASS|FAIL)", prev.get("content") or "") if prev else []
        items = {n for n, _ in checks}
        ok16 = bool(checks) and all(v == "PASS" for _, v in checks) and {"0", "1", "2", "3", "4", "5"} <= items
        res(16, ok16, f"self-check before 'create it'={checks}")
    else:
        res(16, None, "no --chat-session")

    for n, ok, detail in results:
        print({True: "PASS", False: "FAIL", None: "SKIP"}[ok], f"C{n}", detail[:400])
    failed = [n for n, ok, _ in results if ok is False]
    print("SOME FAIL" if failed else "ALL PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MulticaError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(2)
