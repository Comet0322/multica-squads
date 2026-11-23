#!/usr/bin/env python3
"""Drive N hands-off attempts of a benchmark task and score each one.

Usage: bench/run_attempts.py --task T2 --variant v1 --attempts 3
Never touches issue status or comments during a run. A stalled run (no status change for
--stall-min minutes) or an overall timeout is abandoned and still scored (it will fail).
Nothing is deleted. Log: bench/runs/<variant>.log
"""
import argparse, json, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
REPOS = {"T3": "https://github.com/Comet0322/kv-bugs", "T2-hard": "https://github.com/Comet0322/kv-cli"}
TASKFILE = {"T3": ROOT / "tasks" / "T3-fix-interrelated-bugs.md", "T2-hard": ROOT / "tasks" / "T2-hard-store-format-v2.md"}
BRANCH = {"T3": "fix/kv-bugs-{variant}-a{n}", "T2-hard": "feat/kv-format-v2-{variant}-a{n}"}
HIDDEN = {"T3": ROOT / "hidden" / "T3", "T2-hard": ROOT / "hidden" / "T2-hard"}
LOCAL = {"T3": str(Path.home() / "Code" / "kv-bugs"), "T2-hard": str(Path.home() / "Code" / "kv-cli")}


def request(task, n, variant):
    """The task file's requirement section verbatim (GitHub since 2026-11-23), plus the pre-approval
    that lets one chat message stand in for the spec-agreement conversation."""
    body = TASKFILE[task].read_text().split("## Requirement")[1].split("\n", 1)[1].split("\n## ")[0].strip()
    body = (body.replace("<variant>", variant).replace("<attempt>", str(n))
                .replace("forgejo-pr skill", "github-pr skill"))
    return (f"第 {n} 次基準測試(變體 {variant})。Repo: {REPOS[task]}(已在 workspace 註冊),請先 checkout 並閱讀現有程式碼再寫 spec。\n\n"
            f"{body}\n\n"
            "Human gates:只有 PR 這一關。我事先同意你寫出的 spec 與 ticket plan,不要等我回覆、不要問我,直接建立並啟動。")


def sh(*c, **k):
    return subprocess.run(c, capture_output=True, text=True, **k)


def issues():
    # The CLI pages at 50 by default; page through everything so new parents are never missed.
    res, off = [], 0
    while True:
        out = json.loads(sh("multica", "issue", "list", "--output", "json", "--limit", "100", "--offset", str(off)).stdout)
        page = out.get("issues", []) if isinstance(out, dict) else out
        res += page
        if not page or not (isinstance(out, dict) and out.get("has_more")):
            return res
        off += len(page)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True); ap.add_argument("--variant", required=True)
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--stall-min", type=int, default=12); ap.add_argument("--timeout-min", type=int, default=40)
    a = ap.parse_args()
    if a.attempts > 3:
        sys.exit("max 3 attempts per variant")
    (ROOT / "runs").mkdir(exist_ok=True)
    log = (ROOT / "runs" / f"{a.variant}.log").open("a")
    P = lambda *x: (print(*x, flush=True), print(*x, file=log, flush=True))
    sha = sh("git", "-C", str(REPO), "rev-parse", "--short", "HEAD").stdout.strip()
    P(f"== {a.task}/{a.variant} config {sha}")
    for n in range(1, a.attempts + 1):
        known = {i["identifier"] for i in issues()}
        t0 = time.time()
        msg = request(a.task, n, a.variant)
        r = sh(sys.executable, str(REPO / "tools" / "chat.py"), "sq-lead", msg, "--wait", "420")
        P(f"[a{n}] chat done ({int(time.time()-t0)}s): {r.stdout.strip()[:160].replace(chr(10),' ')}")
        new = [i for i in issues() if i["identifier"] not in known and not i.get("parent_issue_id")
               and i.get("assignee_type") == "squad"]
        if not new:
            P(f"[a{n}] ABANDONED: leader created no squad-assigned parent issue"); continue
            continue
        parent = max(new, key=lambda i: i["number"])["identifier"]
        P(f"[a{n}] parent {parent}")
        last, last_change = None, time.time()
        while time.time() - t0 < a.timeout_min * 60:
            fam = [i for i in issues() if i["identifier"] == parent or
                   i.get("parent_issue_id") == next(x["id"] for x in issues() if x["identifier"] == parent)]
            snap = tuple(sorted((i["identifier"], i["status"]) for i in fam))
            if snap != last:
                last, last_change = snap, time.time()
                P(f"[a{n}] {time.strftime('%H:%M:%S')} " + " ".join(f"{k}={v}" for k, v in snap))
            status = dict(snap)[parent]
            subs_open = [k for k, v in snap if k != parent and v not in ("done", "cancelled")]
            if status in ("in_review", "done", "blocked") and not subs_open:
                break
            if time.time() - last_change > a.stall_min * 60:
                P(f"[a{n}] STALLED {a.stall_min} min without change; abandoning"); break
            time.sleep(15)
        else:
            P(f"[a{n}] TIMEOUT {a.timeout_min} min")
        branch = BRANCH[a.task].format(variant=a.variant, n=n)
        s = sh(sys.executable, str(ROOT / "score.py"), parent, "--task", a.task, "--variant", a.variant,
               "--attempt", str(n), "--repo", LOCAL[a.task], "--branch", branch,
               "--hidden", str(HIDDEN[a.task]), "--config-sha", sha)
        P(f"[a{n}] score: {s.stdout.strip()[:600] or s.stderr.strip()[:600]}")
    P(sh(sys.executable, str(ROOT / "report.py"), "--task", a.task).stdout)


main()
