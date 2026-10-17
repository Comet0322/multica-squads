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
    # v6 nests three levels deep (spec -> ticket -> handoff), so the family must be walked
    # transitively. Taking only direct children saw 36 of B1's 74 runs and reported zero
    # rework issues and zero review/QA verdicts, because those all live on handoff issues.
    # `issue list` is capped at 100 rows, so page it.
    everything, off = [], 0
    while True:
        batch = mc("issue", "list", "--limit", "100", "--offset", str(off))
        everything += batch
        off += 100
        if len(batch) < 100:
            break
    by_parent = {}
    for i in everything:
        by_parent.setdefault(i.get("parent_issue_id"), []).append(i)
    family, queue = [parent], [parent["id"]]
    while queue:
        for child in by_parent.get(queue.pop(), []):
            family.append(child)
            queue.append(child["id"])
    # Two kinds of restart must never be conflated: a PERSON stepping in (the run
    # failed) and sq-medic recovering (the squad recovered). A person's action shows
    # up either as a member timeline entry or as a run attributed to `direct_human`
    # -- v4 ACHE-75 proved the second one can leave no timeline entry at all, which
    # is why counting the timeline alone used to miss human wakes.
    human_events, last_end, first = 0, None, None
    human_comment_ids, auto_recoveries, medic_times = set(), 0, []
    reopens = 0
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
                medic_times.append(when)
            # v7 sends work back by reopening the SAME handoff, so a rework cycle is a
            # done -> todo transition, not a new issue. Exact, and no prose is parsed.
            if e.get("action") == "status_changed":
                d = e.get("details") or {}
                if d.get("from") == "done" and d.get("to") in ("todo", "in_progress"):
                    reopens += 1
    runs = []
    for i in family:
        runs += mc("issue", "runs", i["identifier"])
    seen, uniq = set(), []
    for r in runs:
        if r["id"] not in seen:
            seen.add(r["id"]); uniq.append(r)
    run_min = sum((ts(r["completed_at"]) - ts(r["started_at"])).total_seconds() for r in uniq
                  if r.get("completed_at") and r.get("started_at")) / 60
    # A comment-triggered run: one event that produced two wakes. The timing heuristic this
    # replaced counted the DESIGNED rework wake as a violation, because a rework posts the
    # brief and then restarts the issue seconds later. `attribution.evidence.kind` says it
    # exactly: `issue_assignment` for a status-promoted run, `issue_wakeup` for a barrier,
    # `comment` for a comment wake (B1: 30 / 27 / 17 of 74 runs). Human comments are already
    # counted as interventions, so only agent-authored ones are a protocol violation here.
    double_wakes = 0
    for r in uniq:
        at = r.get("attribution") or {}
        if ((at.get("evidence") or {}).get("kind")) != "comment":
            continue
        if ((at.get("evidence") or {}).get("ref_id")) in human_comment_ids:
            continue
        double_wakes += 1
    # A run a person started by hand. `attribution.source` CANNOT be used for this:
    # it names the human or agent at the ROOT of the causal chain, not who started
    # this run. Measured on real data (see bench/failures.md):
    #   human comment -> agent      source=direct_human  ev=comment          sysrule=-
    #   human fires a rule by hand  source=trigger_owner ev=issue_wakeup     sysrule=-
    #   stage barrier, agent family source=delegation    ev=issue_wakeup     sysrule=child_done
    #   stage barrier, human family source=direct_human  ev=issue_wakeup     sysrule=child_done
    #   sq-medic `issue rerun`      source=direct_human  ev=issue_assignment sysrule=-
    # So `direct_human` is both a false positive (a barrier wake in a family a person
    # built) and incomplete (`trigger_owner` is a hand-fire it never mentions).
    # Ask instead what EXPLAINS the run: a platform rule, another agent's task, or
    # sq-medic. A run nothing explains is a person.
    recoveries_matched = 0
    for r in uniq:
        at = r.get("attribution") or {}
        if r.get("wakeup_system_rule"):            # a platform rule fired
            continue
        if at.get("delegated_from_task_id"):       # another agent's task caused it
            continue
        ref = (at.get("evidence") or {}).get("ref_id")
        if ref and ref in human_comment_ids:       # already counted as a member comment
            continue
        started = ts(r.get("started_at"))
        # sq-medic posts its comment and then restarts within seconds; that restart
        # is an automated recovery, already counted in auto_recoveries. At most one
        # restart per Medic comment, which medic's own instructions guarantee.
        if started and recoveries_matched < len(medic_times) and any(
                0 <= (started - m).total_seconds() <= 300 for m in medic_times):
            recoveries_matched += 1
            continue
        human_events += 1
    # `usage` is summed over every request in a run, so cache_read = context size x
    # number of requests and CANNOT measure a context peak on its own (B1: a run with
    # 1,207,032 cache reads had accumulated only 59,797 tokens of context, re-read 20
    # times). cache_write is the context actually accumulated; that is the D-tier metric.
    tokens = peak_in = peak_cache = peak_ctx = 0
    for r in uniq:
        run_in = run_cache = run_ctx = 0
        for u in r.get("usage") or []:
            tokens += u.get("input_tokens", 0) + u.get("output_tokens", 0)
            run_in += u.get("input_tokens", 0) + u.get("output_tokens", 0)
            run_cache += u.get("cache_read_tokens", 0)
            run_ctx += u.get("cache_write_tokens", 0)
        peak_in, peak_cache = max(peak_in, run_in), max(peak_cache, run_cache)
        peak_ctx = max(peak_ctx, run_ctx)
    subs = family[1:]
    stalled = [i["identifier"] for i in subs if i["status"] not in ("done", "cancelled")]
    rework = sum(1 for i in subs if "rework" in i["title"].lower())
    # Direct children of the spec are the tickets AND the spec-check handoff, which is not a
    # ticket; it is the only `internal`-labelled child at that level.
    tickets = [i for i in subs if i.get("parent_issue_id") == parent["id"]
               and not i["title"].lower().startswith("spec-check")]

    rate = existing = clean = None
    if a.repo and a.branch:
        rate, existing, clean = go_tests(a.repo, a.branch, a.hidden)

    # Typed verdicts (the `Verdict` custom property). A property holds only the LATEST
    # value, so it cannot count cycles -- `reopens` does that -- but it is the authoritative
    # final state, read rather than interpreted. In a clean run NOTHING should end negative:
    # a handoff left on CHANGES REQUESTED or FAIL under a ticket that was closed means a
    # failure was closed over. Recorded, not yet part of `success` (that is a rubric change).
    # `Review verdict` and `QA verdict` are separate two-value properties, so the ROLE comes
    # from the property name and nothing has to be guessed from a title (an earlier version
    # keyed it off `title.startswith("qa")`, which no instruction guarantees). The pre-v7
    # `Verdict` property is still read so B1 and earlier stay scoreable; a v7 run that uses
    # it at all is a protocol violation, since its definition is no longer in `properties/`.
    verdicts, negative_final, role_mismatch = {}, 0, []
    for i in family:
        for pr in mc("issue", "property", "list", i["identifier"]) or []:
            name, val = pr.get("name"), pr.get("display")
            if not val or name not in ("Review verdict", "QA verdict", "Verdict"):
                continue
            verdicts[f'{i["identifier"]}/{name}'] = val
            if val in ("CHANGES REQUESTED", "FAIL"):
                negative_final += 1
            if name == "Verdict":
                role_mismatch.append(f'{i["identifier"]}=legacy Verdict:{val}')
            elif val not in (("PASS", "FAIL") if name == "QA verdict"
                             else ("APPROVE", "CHANGES REQUESTED")):
                role_mismatch.append(f'{i["identifier"]}={name}:{val}')

    # Legacy prose counts. These match on the phrase anywhere in a comment, so they
    # OVER-count when a later comment quotes an earlier verdict (measured on B1: 2 real
    # verdicts counted as 3). Kept only so pre-v7 rows stay comparable; for v7 read
    # `reopens` and `verdicts` instead.
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
              "rework_reopens": reopens, "negative_final_verdicts": negative_final,
              "double_wakes": double_wakes, "verdict_role_mismatch": role_mismatch,
              "stalled": stalled}
    print(json.dumps(result, indent=1))
    print("Manual 1-5 (spec_quality, pr_and_handoff_quality, maintainability, scope_discipline): fill in results.csv manual_scores")
    row = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "task": a.task, "variant": a.variant,
           "attempt": a.attempt, "parent": a.parent, "config_sha": a.config_sha,
           "success": int(success), "hidden_pass_rate": "" if rate is None else round(rate, 3),
           "existing_green": int(bool(existing)), "build_clean": int(bool(clean)),
           "human_interventions": human_events, "auto_recoveries": auto_recoveries,
           "stalled_sub_issues": len(stalled), "ticket_count": len(tickets),
           "rework_issues": rework, "rework_reopens": reopens,
           "negative_final_verdicts": negative_final, "double_wakes": double_wakes,
           "verdict_role_mismatch": len(role_mismatch),
           "review_changes_requested": changes_req, "qa_fail": qa_fail,
           "leader_wakeups": sum(1 for r in uniq if r.get("is_leader_task")), "sub_issue_count": len(subs),
           "wall_minutes": round((last_end - first).total_seconds() / 60, 1) if first else "",
           "agent_run_minutes": round(run_min, 1), "tokens": int(tokens),
           "peak_input_tokens": int(peak_in), "peak_cache_read_tokens": int(peak_cache),
           "peak_context_tokens": int(peak_ctx),
           "manual_scores": ""}
    # Full per-agent usage and attribution for every run, so context peaks and who
    # started what stay inspectable without re-querying a run that may age out.
    detail = {"parent": a.parent, "task": a.task, "variant": a.variant, "attempt": a.attempt,
              "config_sha": a.config_sha, "scored_at": row["date"], "result": result,
              "final_verdicts": verdicts,
              "runs": [{"id": r["id"], "issue_id": r.get("issue_id"), "agent_id": r.get("agent_id"),
                        "is_leader_task": r.get("is_leader_task"), "kind": r.get("kind"),
                        "started_at": r.get("started_at"), "completed_at": r.get("completed_at"),
                        "attribution_source": (r.get("attribution") or {}).get("source"),
                        "attribution_evidence_kind": ((r.get("attribution") or {}).get("evidence") or {}).get("kind"),
                        "delegated_from_task_id": (r.get("attribution") or {}).get("delegated_from_task_id"),
                        "wakeup_system_rule": r.get("wakeup_system_rule"),
                        "usage": r.get("usage")} for r in uniq]}
    runs_dir = ROOT / "runs"
    runs_dir.mkdir(exist_ok=True)
    (runs_dir / f"{a.parent}.json").write_text(json.dumps(detail, indent=1))
    print(f"per-run detail: bench/runs/{a.parent}.json")
    path = ROOT / "results.csv"
    # Appending with a header that no longer matches `row` shifts every value against its
    # column name, which reads as plausible nonsense rather than as an error. Refuse instead.
    if path.exists():
        header = next(csv.reader(path.open()), [])
        if header and header != list(row):
            raise SystemExit(
                "bench/results.csv header does not match the scorer's columns.\n"
                f"  file:   {','.join(header)}\n  scorer: {','.join(row)}\n"
                "Rewrite the file with the new columns before scoring.")
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if not path.exists() or path.stat().st_size == 0:
            w.writeheader()
        w.writerow(row)


main()
