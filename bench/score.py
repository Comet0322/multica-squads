#!/usr/bin/env python3
"""Score a finished squad run.

Usage: bench/score.py <PARENT-ISSUE-ID> [--hidden DIR --repo PATH --branch NAME] [--task T2] [--config-sha SHA]

Auto-scores what can be measured from Multica (timeline actors, runs, usage) and,
when --hidden/--repo/--branch are given, runs hidden Go tests against the branch.
Manual items are printed as TODO and left out of the auto subtotal.
Appends a row to bench/results.csv.
"""
import argparse, csv, json, subprocess, tempfile, shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUBRIC = json.loads((ROOT / "rubric.json").read_text())


def mc(*a):
    p = subprocess.run(["multica", *a, "--output", "json"], capture_output=True, text=True)
    if p.returncode:
        raise SystemExit(p.stderr)
    out = json.loads(p.stdout or "null")
    if isinstance(out, dict) and a[1] == "list":
        out = next((v for v in out.values() if isinstance(v, list)), out)
    return out


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def go_tests(repo, branch, hidden):
    """Return (hidden_pass_rate, existing_green, build_clean)."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "-C", repo, "fetch", "-q", "origin"], check=True)
        subprocess.run(["git", "-C", repo, "worktree", "add", "-q", "--detach", str(tmp / "wt"), f"origin/{branch}"], check=True)
        wt = tmp / "wt"
        sh = lambda *c: subprocess.run(c, cwd=wt, capture_output=True, text=True)
        existing = sh("go", "test", "-count=1", "./...").returncode == 0
        clean = sh("go", "build", "./...").returncode == 0 and sh("go", "vet", "./...").returncode == 0 \
            and not sh("gofmt", "-l", ".").stdout.strip()
        rate = None
        if hidden and Path(hidden).exists() and any(Path(hidden).rglob("*_test.go")):
            shutil.copytree(hidden, wt, dirs_exist_ok=True)
            r = sh("go", "test", "-count=1", "-json", "./...")
            passed = failed = 0
            for line in r.stdout.splitlines():
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("Test") and e.get("Action") == "pass":
                    passed += 1
                elif e.get("Test") and e.get("Action") == "fail":
                    failed += 1
            rate = passed / (passed + failed) if passed + failed else 0.0
        return rate, existing, clean
    finally:
        subprocess.run(["git", "-C", repo, "worktree", "prune"], capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parent"); ap.add_argument("--task", default="")
    ap.add_argument("--hidden"); ap.add_argument("--repo"); ap.add_argument("--branch")
    ap.add_argument("--config-sha", default="")
    a = ap.parse_args()

    parent = mc("issue", "get", a.parent)
    family = [parent] + [i for i in mc("issue", "list") if i.get("parent_issue_id") == parent["id"]]
    human_events, last_end, first = 0, None, None
    for i in family:
        for e in mc("issue", "timeline", i["identifier"]):
            when = ts(e.get("created_at"))
            first = min(first, when) if first else when
            last_end = max(last_end, when) if last_end else when
            is_human = e.get("actor_type") == "member"
            # The requirement/approval chat is outside the issue timeline; any member
            # activity here (status change or comment) is an intervention.
            if is_human and (e.get("action") == "status_changed" or e.get("type") == "comment"):
                human_events += 1
    runs = []
    for i in family:
        runs += mc("issue", "runs", i["identifier"])
    seen, uniq = set(), []
    for r in runs:
        if r["id"] not in seen:
            seen.add(r["id"]); uniq.append(r)
    run_min = sum((ts(r["completed_at"]) - ts(r["started_at"])).total_seconds() for r in uniq
                  if r.get("completed_at") and r.get("started_at")) / 60
    tokens = 0
    for r in uniq:
        for u in r.get("usage") or []:
            tokens += u.get("input_tokens", 0) + u.get("output_tokens", 0)
    subs = family[1:]
    stalled = [i["identifier"] for i in subs if i["status"] not in ("done", "cancelled")]
    rework = sum(1 for i in subs if i["title"].lower().startswith("rework"))

    rate = existing = clean = None
    if a.repo and a.branch:
        rate, existing, clean = go_tests(a.repo, a.branch, a.hidden)

    q, au = RUBRIC["quality"]["items"], RUBRIC["autonomy"]["items"]
    score = {}
    score["hidden_tests"] = None if rate is None else round(rate * q["hidden_tests"]["max"], 1)
    score["existing_tests_green"] = None if existing is None else (10 if existing else 0)
    score["build_vet_gofmt"] = None if clean is None else (5 if clean else 0)
    score["zero_intervention"] = max(0, 15 - 5 * human_events)
    score["no_unexpected_stall"] = 0 if stalled else 10
    auto_total = sum(v for v in score.values() if v is not None)
    gate = RUBRIC["failure_gate"]
    failed = (rate is not None and rate < gate["hidden_pass_rate_below"]) or human_events >= gate["interventions_at_least"]

    print(json.dumps({"parent": a.parent, "auto_scores": score, "auto_subtotal": auto_total,
                      "human_interventions": human_events, "stalled": stalled, "failed_gate": failed}, indent=1))
    print("TODO manual: no_out_of_scope_changes(5), no_routine_questions(5), spec_quality(10), pr_and_handoff_quality(10), maintainability(10)")
    row = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "task": a.task, "parent": a.parent,
           "config_sha": a.config_sha, "labels": ",".join(l["name"] for l in parent.get("labels", [])),
           "auto_subtotal": auto_total, "interventions": human_events, "failed_gate": failed,
           "wall_minutes": round((last_end - first).total_seconds() / 60, 1) if first else "",
           "agent_run_minutes": round(run_min, 1), "leader_wakeups": sum(1 for r in uniq if r.get("is_leader_task")),
           "rework_issues": rework, "tokens": int(tokens), "sub_issues": len(subs), "manual_scores": ""}
    path = ROOT / "results.csv"
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row)); 
        if new: w.writeheader()
        w.writerow(row)


main()
