#!/usr/bin/env python3
"""Watch one squad run without relying on `issue children`.

Usage: bench/watch.py <spec-issue-id> [--stall-min 12] [--timeout-min 60] [--poke-max 0]
Reports FINISHED / STALLED / TIMEOUT explicitly. A poke (member comment) counts as a human
intervention and is only sent when --poke-max > 0 and the run has been idle past --stall-min.
"""
import argparse, json, subprocess, sys, time

def mc(*a):
    p = subprocess.run(["multica", *a, "--output", "json"], capture_output=True, text=True)
    return json.loads(p.stdout or "null") if p.returncode == 0 else None

def all_issues():
    res, off = [], 0
    while True:
        o = mc("issue", "list", "--limit", "100", "--offset", str(off))
        page = o.get("issues", []) if isinstance(o, dict) else (o or [])
        res += page
        if not page or not (isinstance(o, dict) and o.get("has_more")):
            return res
        off += len(page)

def family(spec_ident):
    iss = all_issues()
    by_id = {i["id"]: i for i in iss}
    spec = next(i for i in iss if i["identifier"] == spec_ident)
    fam, frontier = {spec["id"]: spec}, [spec["id"]]
    while frontier:
        nxt = [i["id"] for i in iss if i.get("parent_issue_id") in frontier and i["id"] not in fam]
        for k in nxt: fam[k] = by_id[k]
        frontier = nxt
    return spec, list(fam.values())

def active_runs(spec_id_list):
    n = 0
    for iid in spec_id_list:
        r = mc("issue", "runs", iid) or []
        r = r if isinstance(r, list) else next((v for v in r.values() if isinstance(v, list)), [])
        n += sum(1 for x in r if x["status"] in ("queued", "dispatched", "running", "waiting_local_directory"))
    return n

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("spec")
    ap.add_argument("--stall-min", type=int, default=12); ap.add_argument("--timeout-min", type=int, default=60)
    ap.add_argument("--poke-max", type=int, default=0)
    a = ap.parse_args()
    t0, last, last_change, pokes = time.time(), None, time.time(), 0
    while True:
        spec, fam = family(a.spec)
        snap = tuple(sorted((i["identifier"], i["status"]) for i in fam))
        if snap != last:
            last, last_change = snap, time.time()
            print(time.strftime("%H:%M:%S"), f"issues={len(fam)}", " ".join(f"{k}={v}" for k, v in snap if v not in ("done", "cancelled", "backlog")) or "-", flush=True)
        done_all = all(i["status"] in ("done", "cancelled") for i in fam if i["id"] != spec["id"])
        if spec["status"] in ("in_review", "done", "blocked") and done_all and len(fam) > 1:
            print(f"FINISHED spec={spec['status']} pokes={pokes} issues={len(fam)}"); return
        idle = time.time() - last_change
        if idle > a.stall_min * 60 and active_runs([i["id"] for i in fam]) == 0:
            if pokes < a.poke_max:
                subprocess.run(["multica", "issue", "comment", "add", a.spec, "--content",
                                "The run looks idle. Check the ticket and handoff issues and advance whatever is ready."], capture_output=True)
                pokes += 1; last_change = time.time(); print(f"POKED {pokes}", flush=True)
            else:
                print(f"STALLED idle={int(idle/60)}min spec={spec['status']} pokes={pokes}"); return
        if time.time() - t0 > a.timeout_min * 60:
            print(f"TIMEOUT {a.timeout_min}min (not finished) spec={spec['status']} pokes={pokes}"); return
        time.sleep(20)

main()
