#!/usr/bin/env python3
"""Sync agents, skills, MCP servers and squads in this directory to Multica.

Idempotent: resources are matched by name; existing ones are updated.
Order: properties -> skills -> mcp -> agents -> squads. Never deletes anything.

Target workspaces come from workspaces.json ({"workspaces": ["slug", ...]} or
{"workspaces": "all"} for every workspace where you are admin/owner). Override
with repeated --workspace. Workspaces where you are not admin/owner are skipped.

Usage: ./sync.py [--dry-run] [--workspace ID|SLUG ...] [--only properties,skills,mcp,agents,squads]
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARGS = None
WS = None
TIERS = json.loads((ROOT / "tiers.json").read_text())


def run(*cmd, read_only=False):
    full = ["multica", *cmd]
    if WS:
        full += ["--workspace-id", WS]
    if ARGS.dry_run and not read_only:
        print("  [dry-run]", " ".join(full))
        return None
    p = subprocess.run(full, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"FAILED: {' '.join(full)}\n{p.stderr or p.stdout}")
    out = p.stdout.strip()
    try:
        return json.loads(out) if out else None
    except json.JSONDecodeError:
        return out


def listing(*cmd):
    out = run(*cmd, "--output", "json", read_only=True) or []
    if isinstance(out, dict):
        out = next((v for v in out.values() if isinstance(v, list)), [])
    return out


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta


def sync_skills():
    existing = {s["name"]: s for s in listing("skill", "list")}
    ids = {n: s["id"] for n, s in existing.items()}
    for d in sorted((ROOT / "skills").glob("*/")):
        main = d / "SKILL.md"
        if not main.exists():
            continue
        meta = frontmatter(main.read_text())
        name, desc = meta.get("name", d.name), meta.get("description", "")
        if name in existing:
            print(f"skill update: {name}")
            run("skill", "update", existing[name]["id"], "--description", desc,
                "--content-file", str(main))
            sid = existing[name]["id"]
        else:
            print(f"skill create: {name}")
            r = run("skill", "create", "--name", name, "--description", desc,
                    "--content-file", str(main))
            sid = r["id"] if r else f"<{name}>"
        ids[name] = sid
        for f in sorted(p for p in d.rglob("*") if p.is_file() and p != main):
            rel = f.relative_to(d).as_posix()
            print(f"  file: {rel}")
            run("skill", "files", "upsert", sid, "--path", rel, "--content-file", str(f))
    return ids


def sync_mcp():
    existing = {s["name"]: s for s in listing("workspace", "mcp", "list")}
    ids = {n: s["id"] for n, s in existing.items()}
    for f in sorted((ROOT / "mcp").glob("*.json")):
        name = f.name.removesuffix(".local.json").removesuffix(".json")
        if name in existing:
            print(f"mcp update: {name}")
            run("workspace", "mcp", "update", existing[name]["id"],
                "--server-config-file", str(f))
            ids[name] = existing[name]["id"]
        else:
            print(f"mcp add: {name}")
            r = run("workspace", "mcp", "add", name, "--server-config-file", str(f))
            ids[name] = r["id"] if r else f"<{name}>"
    return ids


def sync_agents(skill_ids, mcp_ids):
    runtimes = {}
    for r in listing("runtime", "list"):
        runtimes.setdefault(r["provider"], r["id"])
    existing = {a["name"]: a for a in listing("agent", "list") if not a.get("archived_at")}
    ids = {n: a["id"] for n, a in existing.items()}
    for f in sorted((ROOT / "agents").glob("*.json")):
        cfg = json.loads(f.read_text())
        name = cfg["name"]
        instr = f.with_suffix(".md").read_text().strip() if f.with_suffix(".md").exists() else ""
        if "tier" in cfg:
            cfg = {**cfg, **{k: v for k, v in TIERS[cfg["tier"]].items() if k in ("model", "thinking_level")}}
        rt = runtimes.get(cfg["runtime"])
        if not rt:
            print(f"agent SKIP: {name} (no online '{cfg['runtime']}' runtime in this workspace)")
            continue
        flags = ["--description", cfg.get("description", ""), "--instructions", instr,
                 "--max-concurrent-tasks", str(cfg.get("max_concurrent_tasks", 6)),
                 "--model", cfg.get("model", ""),
                 "--thinking-level", cfg.get("thinking_level", "")]
        if name in existing:
            print(f"agent update: {name}")
            aid = existing[name]["id"]
            run("agent", "update", aid, "--runtime-id", rt, *flags)
        else:
            print(f"agent create: {name}")
            r = run("agent", "create", "--name", name, "--runtime-id", rt, *flags)
            aid = r["id"] if r else f"<{name}>"
        ids[name] = aid
        sk = [skill_ids[s] for s in cfg.get("skills", [])]
        run("agent", "skills", "set", aid, "--skill-ids", ",".join(sk))
        for m in cfg.get("mcp", []):
            run("agent", "mcp", "add", aid, mcp_ids[m])
    return ids


def sync_squads(agent_ids):
    existing = {s["name"]: s for s in listing("squad", "list")}
    for f in sorted((ROOT / "squads").glob("*.json")):
        cfg = json.loads(f.read_text())
        name = cfg["name"]
        need = [cfg["leader"]] + [m["agent"] for m in cfg.get("members", [])]
        if missing := [n for n in need if n not in agent_ids]:
            print(f"squad SKIP: {name} (missing agents: {', '.join(missing)})")
            continue
        instr = f.with_suffix(".md").read_text().strip() if f.with_suffix(".md").exists() else ""
        if name in existing:
            print(f"squad update: {name}")
            sid = existing[name]["id"]
            run("squad", "update", sid, "--description", cfg.get("description", ""),
                "--instructions", instr, "--leader", cfg["leader"])
        else:
            print(f"squad create: {name}")
            r = run("squad", "create", "--name", name, "--leader", cfg["leader"],
                    "--description", cfg.get("description", ""))
            sid = r["id"] if r else f"<{name}>"
            run("squad", "update", sid, "--instructions", instr)
        have = {m["member_id"]: m for m in (listing("squad", "member", "list", sid) if not ARGS.dry_run or name in existing else [])}
        for m in cfg.get("members", []):
            aid = agent_ids[m["agent"]]
            if aid in have:
                if have[aid].get("role") != m["role"]:
                    run("squad", "member", "set-role", sid, "--member-id", aid, "--role", m["role"])
            else:
                print(f"  member add: {m['agent']} ({m['role']})")
                run("squad", "member", "add", sid, "--member-id", aid, "--role", m["role"])


def me():
    p = subprocess.run(["multica", "auth", "status"], capture_output=True, text=True)
    out = p.stdout + p.stderr
    m = re.search(r"\(([^)]+@[^)]+)\)", out)
    return m.group(1) if m else None


def target_workspaces():
    all_ws = json.loads(subprocess.run(["multica", "workspace", "list", "--output", "json"],
                                       capture_output=True, text=True, check=True).stdout)
    if ARGS.workspace:
        want = ARGS.workspace
    else:
        want = json.loads((ROOT / "workspaces.json").read_text())["workspaces"]
    if want == "all":
        return all_ws
    sel = [w for w in all_ws if w["id"] in want or w["slug"] in want or w["name"] in want]
    for x in want:
        if not any(x in (w["id"], w["slug"], w["name"]) for w in sel):
            print(f"WARN: workspace '{x}' not found or not accessible")
    return sel


def is_admin(email):
    global WS
    members = listing("workspace", "member", "list")
    return any(m["email"] == email and m["role"] in ("owner", "admin") for m in members)


def sync_workspace(only):
    skills = sync_skills() if "skills" in only else {s["name"]: s["id"] for s in listing("skill", "list")}
    mcp = sync_mcp() if "mcp" in only else {s["name"]: s["id"] for s in listing("workspace", "mcp", "list")}
    agents = sync_agents(skills, mcp) if "agents" in only else {a["name"]: a["id"] for a in listing("agent", "list")}
    if "squads" in only:
        sync_squads(agents)
    if "properties" in only:
        sync_properties()


def sync_properties():
    """Workspace custom property definitions. Creating them is owner/admin only, so they
    belong in config rather than in an agent's hands; agents only set VALUES on issues."""
    existing = {d["name"]: d for d in listing("property", "list")}
    for f in sorted((ROOT / "properties").glob("*.json")):
        cfg = json.loads(f.read_text())
        name = cfg["name"]
        flags = ["--description", cfg.get("description", ""), "--icon", cfg.get("icon", "")]
        if name in existing:
            print(f"property update: {name}")
            run("property", "update", existing[name]["id"], *flags)
            continue
        print(f"property create: {name}")
        opts = []
        for o in cfg.get("options", []):
            opts += ["--option", o]
        run("property", "create", "--name", name, "--type", cfg["type"], *flags, *opts)


def main():
    global ARGS, WS
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workspace", action="append", help="ID, slug or name; repeatable")
    ap.add_argument("--only", default="properties,skills,mcp,agents,squads")
    ARGS = ap.parse_args()
    only = set(ARGS.only.split(","))
    email = me()
    for w in target_workspaces():
        WS = w["id"]
        print(f"\n=== workspace {w['name']} ({w['slug']})")
        if not is_admin(email):
            print("SKIP: you are not admin/owner here")
            continue
        sync_workspace(only)


main()
