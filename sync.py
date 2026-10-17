#!/usr/bin/env python3
"""Sync agents, skills, MCP servers and squads in this directory to Multica.

Idempotent: resources are matched by name; existing ones are updated.
Order: skills -> mcp -> agents -> squads. Never deletes anything.

Usage: ./sync.py [--dry-run] [--workspace ID|SLUG] [--only skills,mcp,agents,squads]
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARGS = None


def run(*cmd, read_only=False):
    full = ["multica", *cmd]
    if ARGS.workspace:
        full += ["--workspace-id", ARGS.workspace]
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
    return run(*cmd, "--output", "json", read_only=True) or []


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
        rt = runtimes.get(cfg["runtime"]) or sys.exit(f"no runtime for provider {cfg['runtime']}")
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


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workspace")
    ap.add_argument("--only", default="skills,mcp,agents,squads")
    ARGS = ap.parse_args()
    only = set(ARGS.only.split(","))
    skills = sync_skills() if "skills" in only else {s["name"]: s["id"] for s in listing("skill", "list")}
    mcp = sync_mcp() if "mcp" in only else {s["name"]: s["id"] for s in listing("workspace", "mcp", "list")}
    agents = sync_agents(skills, mcp) if "agents" in only else {a["name"]: a["id"] for a in listing("agent", "list")}
    if "squads" in only:
        sync_squads(agents)


main()
