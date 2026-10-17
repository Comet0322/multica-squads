#!/usr/bin/env python3
"""Score a finished squad run.

Usage: bench/score.py <PARENT-ISSUE-ID> --task T2 --variant NAME [--attempt N] [--hidden DIR --repo PATH --branch NAME] [--config-sha SHA]

Records one run (success/fail per bench/rubric.json plus process and cost metrics) as a
row in bench/results.csv. Aggregate with bench/report.py. Manual 1-5 ratings are filled later
in the csv (manual_scores column).
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
    ap.add_argument("parent"); ap.add_argument("--task", required=True)
    ap.add_argument("--variant", required=True); ap.add_argument("--attempt", type=int, default=1)
    ap.add_argument("--hidden"); ap.add_argument("--repo"); ap.add_argument("--branch")
    ap.add_argument("--config-sha", default="")
    a = ap.parse_args()

    parent = mc("issue", "get", a.parent)
    family = [parent] + [i for i in mc("issue", "list") if i.get("parent_issue_id") == parent["id"]]
    # Two kinds of restart must never be conflated: a PERSON stepping in (the run
    # failed) and sq-medic recovering (the squad recovered). A person's action shows
    # up either as a member timeline entry or as a run attributed to `direct_human`
    # -- v4 ACHE-75 proved the second one can leave no timeline entry at all, which
    # is why counting the timeline alone used to miss human wakes.
    human_events, last_end, first = 0, None, None
    human_comment_ids, auto_recoveries = set(), 0
    for i in family:
        for e in mc("issue", "timeline", i["identifier"]):
            when = ts(e.get("created_at"))
            first = min(first, when) if first else when
            last_end = max(last_end, when) if last_end else when
            is_human = e.get("actor_type") == "member"
            body = (e.get("content") or "") if e.get("type") == "comment" else ""
            # The requirement/approval chat is outside the issue timeline; any member
            # activity here (status change or comment) is an intervention.
            if is_human and (e.get("action") == "status_changed" or e.get("type") == "comment"):
                human_events += 1
                if e.get("type") == "comment":
                    human_comment_ids.add(e.get("id"))
            if not is_human and body.startswith("**Medic**"):
                auto_recoveries += 1
    runs = []
    for i in family:
        runs += mc("issue", "runs", i["identifier"])
    seen, uniq = set(), []
    for r in runs:
        if r["id"] not in seen:
            seen.add(r["id"]); uniq.append(r)
    run_min = sum((ts(r["completed_at"]) - ts(r["started_at"])).total_seconds() for r in uniq
                  if r.get("completed_at") and r.get("started_at")) / 60
    # A run a person started by hand. Dedupe against the member comments already
    # counted above: one human comment produces both a timeline entry and a run.
    for r in uniq:
        at = r.get("attribution") or {}
        if at.get("source") != "direct_human":
            continue
        ref = (at.get("evidence") or {}).get("ref_id")
        if ref and ref in human_comment_ids:
            continue
        human_events += 1
    tokens = peak_in = peak_cache = 0
    for r in uniq:
        run_in = run_cache = 0
        for u in r.get("usage") or []:
            tokens += u.get("input_tokens", 0) + u.get("output_tokens", 0)
            run_in += u.get("input_tokens", 0) + u.get("output_tokens", 0)
            run_cache += u.get("cache_read_tokens", 0)
        peak_in, peak_cache = max(peak_in, run_in), max(peak_cache, run_cache)
    subs = family[1:]
    stalled = [i["identifier"] for i in subs if i["status"] not in ("done", "cancelled")]
    rework = sum(1 for i in subs if "rework" in i["title"].lower())

    rate = existing = clean = None
    if a.repo and a.branch:
        rate, existing, clean = go_tests(a.repo, a.branch, a.hidden)

    # Process metrics from comments: reviewer / QA verdicts.
    changes_req = qa_fail = 0
    for i in subs:
        for e in mc("issue", "timeline", i["identifier"]):
            body = (e.get("content") or "") if e.get("type") == "comment" else ""
            if "CHANGES REQUESTED" in body.upper() and "VERDICT" in body.upper():
                changes_req += 1
            if "QA VERDICT: FAIL" in body.upper() or "VERDICT: FAIL" in body.upper():
                qa_fail += 1

    cap = RUBRIC["success"].get("max_auto_recoveries", 3)
    success = (rate == 1.0 if rate is not None else False) and bool(existing) and bool(clean) \
        and human_events == 0 and auto_recoveries <= cap and not stalled
    result = {"parent": a.parent, "success": success, "hidden_pass_rate": rate,
              "existing_green": existing, "build_clean": clean,
              "human_interventions": human_events, "auto_recoveries": auto_recoveries,
              "stalled": stalled}
    print(json.dumps(result, indent=1))
    print("Manual 1-5 (spec_quality, pr_and_handoff_quality, maintainability, scope_discipline): fill in results.csv manual_scores")
    row = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "task": a.task, "variant": a.variant,
           "attempt": a.attempt, "parent": a.parent, "config_sha": a.config_sha,
           "success": int(success), "hidden_pass_rate": "" if rate is None else round(rate, 3),
           "existing_green": int(bool(existing)), "build_clean": int(bool(clean)),
           "human_interventions": human_events, "auto_recoveries": auto_recoveries,
           "stalled_sub_issues": len(stalled),
           "rework_issues": rework, "review_changes_requested": changes_req, "qa_fail": qa_fail,
           "leader_wakeups": sum(1 for r in uniq if r.get("is_leader_task")), "sub_issue_count": len(subs),
           "wall_minutes": round((last_end - first).total_seconds() / 60, 1) if first else "",
           "agent_run_minutes": round(run_min, 1), "tokens": int(tokens),
           "peak_input_tokens": int(peak_in), "peak_cache_read_tokens": int(peak_cache),
           "manual_scores": ""}
    # Full per-agent usage and attribution for every run, so context peaks and who
    # started what stay inspectable without re-querying a run that may age out.
    detail = {"parent": a.parent, "task": a.task, "variant": a.variant, "attempt": a.attempt,
              "config_sha": a.config_sha, "scored_at": row["date"], "result": result,
              "runs": [{"id": r["id"], "issue_id": r.get("issue_id"), "agent_id": r.get("agent_id"),
                        "is_leader_task": r.get("is_leader_task"), "kind": r.get("kind"),
                        "started_at": r.get("started_at"), "completed_at": r.get("completed_at"),
                        "attribution_source": (r.get("attribution") or {}).get("source"),
                        "wakeup_system_rule": r.get("wakeup_system_rule"),
                        "usage": r.get("usage")} for r in uniq]}
    runs_dir = ROOT / "runs"
    runs_dir.mkdir(exist_ok=True)
    (runs_dir / f"{a.parent}.json").write_text(json.dumps(detail, indent=1))
    print(f"per-run detail: bench/runs/{a.parent}.json")
    path = ROOT / "results.csv"
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)


main()
