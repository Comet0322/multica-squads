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
REQ = {
 "T2": """第 {n} 次基準測試(變體 {variant})。請在 workspace 已註冊的 repo kv-cli(http://127.0.0.1:13000/squadadmin/kv-cli.git)上新增功能,請先 checkout 並閱讀現有程式碼再寫 spec。
需求:新增 `kv export` 與 `kv import`。
- `kv export`:把整個 store 以單一 JSON 物件 {{"key":"value",...}} 印到 stdout,key 依字母排序,exit 0;空 store 印 `{{}}`。
- `kv import`:從 stdin 讀一個 JSON 物件,把每個 key 寫入(覆蓋已存在的 key、保留其他 key)。無效 JSON 或值不是字串:stderr 報錯、exit 1、store 完全不變(要么全部成功要么全部不寫)。
- 既有指令與其 exit code 不可改變。README 要說明這兩個指令。
流程:所有工作在 feature branch feat/kv-export-import-{variant}-a{n} 上(從 main 開出,不直接動 main);階段為實作、review、QA、文件,最後 stage 5 由 sq-implementer 用 forgejo-pr skill 對 main 開 PR(描述含 'Closes <parent issue 編號>' 與具體 sub-issue 編號及判定)。**不要 merge PR**。Human gates:只有 PR 這一關,PR 開好後 parent 設為 in_review。其餘全程自主、不要問我。我同意這份需求與流程,請直接寫 spec、建 parent 與 sub-issue 並啟動。""",
}
BRANCH = {"T2": "feat/kv-export-import-{variant}-a{n}"}
HIDDEN = {"T2": ROOT / "hidden" / "T2"}
LOCAL = {"T2": "/home/comet/Code/kv-cli"}


def sh(*c, **k):
    return subprocess.run(c, capture_output=True, text=True, **k)


def issues():
    out = json.loads(sh("multica", "issue", "list", "--output", "json").stdout)
    return out.get("issues", out) if isinstance(out, dict) else out


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
        msg = REQ[a.task].format(n=n, variant=a.variant)
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
