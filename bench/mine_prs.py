#!/usr/bin/env python3
"""Mine candidate benchmark tasks from real merged PRs (SWE-bench construction, bigger PRs).

A candidate is a merged PR that (a) closes an issue, so a requirement text exists, (b) changes
tests, so hidden tests exist, (c) is mid-sized: several files and a few hundred lines, so the
work cannot be one edit, and (d) is recent, to lower the chance a model has seen the answer.

This only LISTS candidates. Validating one (tests fail at the base commit, pass at the merge
commit, in the runtime container) is a separate step. Read-only: public GitHub data via `gh`.

  bench/mine_prs.py --since 2026-08-01 [--min-add 80 --max-add 700 --min-files 3 --max-files 12] owner/repo ...
"""
import argparse, json, subprocess, sys

Q = """query($o:String!,$n:String!){repository(owner:$o,name:$n){
  licenseInfo{spdxId} primaryLanguage{name} pushedAt
  pullRequests(states:MERGED,first:100,orderBy:{field:UPDATED_AT,direction:DESC}){nodes{
    number title url mergedAt baseRefOid mergeCommit{oid}
    additions deletions changedFiles
    closingIssuesReferences(first:3){nodes{number title}}
    files(first:40){nodes{path}}}}}}"""

def gql(owner, name):
    p = subprocess.run(["gh", "api", "graphql", "-f", f"query={Q}", "-F", f"o={owner}", "-F", f"n={name}"],
                       capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr.strip()[:200])
    return json.loads(p.stdout)["data"]["repository"]

def is_test(path):
    s = path.lower()
    return "/tests/" in "/" + s or "/test_" in "/" + s or s.endswith("_test.py") or "/testing/" in "/" + s

def is_doc(path):
    return path.lower().endswith((".md", ".rst", ".txt")) or path.startswith(("docs/", "doc/"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="+")
    ap.add_argument("--since", default="2026-08-01")
    ap.add_argument("--min-add", type=int, default=80)
    ap.add_argument("--max-add", type=int, default=700)
    ap.add_argument("--min-files", type=int, default=3)
    ap.add_argument("--max-files", type=int, default=12)
    a = ap.parse_args()
    rows = []
    for full in a.repos:
        o, n = full.split("/")
        try:
            r = gql(o, n)
        except Exception as e:
            print(f"SKIP {full}: {e}", file=sys.stderr); continue
        lic = (r["licenseInfo"] or {}).get("spdxId")
        for pr in r["pullRequests"]["nodes"]:
            if not pr["mergedAt"] or pr["mergedAt"][:10] < a.since:
                continue
            issues = pr["closingIssuesReferences"]["nodes"]
            files = [f["path"] for f in pr["files"]["nodes"]]
            tests = [f for f in files if is_test(f)]
            src = [f for f in files if not is_test(f) and not is_doc(f)]
            if not issues or not tests or not src:
                continue
            if not (a.min_files <= pr["changedFiles"] <= a.max_files):
                continue
            if not (a.min_add <= pr["additions"] <= a.max_add):
                continue
            rows.append(dict(repo=full, lic=lic, pr=pr["number"], merged=pr["mergedAt"][:10], add=pr["additions"],
                             dele=pr["deletions"], files=pr["changedFiles"], src=len(src), tests=len(tests),
                             issue=issues[0]["number"], title=pr["title"][:70], url=pr["url"]))
    rows.sort(key=lambda r: (r["repo"], -r["add"]))
    print(f"{'repo':28} {'PR':>6} {'merged':10} {'+':>4} {'-':>4} {'files':>5} {'src/test':>8} {'issue':>6} {'lic':8} title")
    for r in rows:
        print(f"{r['repo']:28} {r['pr']:>6} {r['merged']:10} {r['add']:>4} {r['dele']:>4} {r['files']:>5} "
              f"{str(r['src'])+'/'+str(r['tests']):>8} {r['issue']:>6} {str(r['lic']):8} {r['title']}")
    print(f"\n{len(rows)} candidates", file=sys.stderr)

if __name__ == "__main__":
    main()
