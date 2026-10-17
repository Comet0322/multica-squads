#!/usr/bin/env python3
"""Aggregate bench/results.csv per (task, variant): pass^n, pass@n and mean cost/process metrics.

Usage: bench/report.py [--task T2]
At most 3 runs per variant are expected (see rubric.json); more rows are reported but flagged.
"""
import argparse, csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument("--task"); a = ap.parse_args()
rows = list(csv.DictReader((ROOT / "results.csv").open()))
groups = defaultdict(list)
for r in rows:
    if not a.task or r["task"] == a.task:
        groups[(r["task"], r["variant"])].append(r)

num = lambda r, k: float(r[k]) if r[k] not in ("", None) else 0.0
# Two rework columns, because the mechanism changed: pre-v7 sent work back as a NEW
# `rework` issue, v7+ reopens the stage in place. One column reads 0 on the other's runs.
print(f"{'task':6} {'variant':18} {'n':>2} {'succ':>4} {'pass^n':>7} {'pass@n':>7} {'interv':>6} {'rwIss':>6} {'rwOpen':>6} {'wake':>5} {'min':>6} {'tokens':>9}")
for (task, variant), rs in sorted(groups.items()):
    n, ok = len(rs), sum(int(r["success"]) for r in rs)
    mean = lambda k: sum(num(r, k) for r in rs) / n
    flag = "  (>3 runs)" if n > 3 else ""
    print(f"{task:6} {variant:18} {n:>2} {ok:>4} {str(ok == n):>7} {str(ok > 0):>7} {mean('human_interventions'):>6.1f} "
          f"{mean('rework_issues'):>6.1f} {mean('rework_reopens'):>6.1f} {mean('leader_wakeups'):>5.1f} {mean('agent_run_minutes'):>6.1f} {mean('tokens'):>9.0f}{flag}")
