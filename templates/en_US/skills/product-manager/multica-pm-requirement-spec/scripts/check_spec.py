#!/usr/bin/env python3
"""Check an Issue / spec against references/spec-template.md. Python 3.9+, stdlib only.

  check_spec.py draft.md            check a file ("-" reads stdin)
  check_spec.py --issue TEST-14     fetch the description with `multica issue get`
  check_spec.py --sync-check FILE   verify FILE's fenced template block equals the canonical one

Exit 0 = PASS, 1 = FAIL (one line per problem), 2 = usage / fetch error.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CANON = Path(__file__).resolve().parent.parent / "references" / "spec-template.md"
SECTIONS = ["issue source", "background", "goal", "scope", "non-goals",
            "acceptance criteria", "open questions", "references", "notes"]
VAGUE = re.compile(r"\b(etc\.?|and so on|appropriate(ly)?|relevant|as needed|user-friendly|TBD|TODO|a bit)\b", re.I)
ENDS = ["design", "frontend", "backend", "testing"]


def sections(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            name = m.group(1).lower()
            cur = next((s for s in SECTIONS if name.startswith(s)), None)
            if cur:
                out[cur] = []
            continue
        if cur:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def check(text):
    errs = []
    sec = sections(text)
    for name in ("issue source", "scope"):
        if name not in sec:
            errs.append("missing section '## %s'" % name.title())
    if errs:
        return errs
    src = sec["issue source"]
    ticked = re.findall(r"^\s*-\s*\[[xX]\]\s*(External|Fully self-contained)", src, re.M)
    if len(ticked) != 1:
        errs.append("Issue Source: tick exactly one box (External system link / Fully self-contained), found %d" % len(ticked))
    external = ticked == ["External"]
    ends = re.findall(r"^\s*-\s*\[[xX]\]\s*(Design|Frontend|Backend|Testing)\b", sec["scope"], re.M | re.I)
    if not ends:
        errs.append("Scope: tick at least one involved end (Design / Frontend / Backend / Testing)")
    if external:
        if not re.search(r"https?://\S+", src):
            errs.append("Issue Source: external link is ticked but no URL is given")
        if not re.search(r"Summary:\s*\S", src):
            errs.append("Issue Source: external link needs a one-line 'Summary:'")
        return errs
    for name in ("background", "goal", "non-goals"):
        if not sec.get(name):
            errs.append("section '%s' is empty (self-contained Issues must fill it)" % name.title())
    if not re.search(r"Changes:\s*\S", sec["scope"]):
        errs.append("Scope: 'Changes:' is empty")
    ac = sec.get("acceptance criteria", "")
    items = re.findall(r"^\s*-\s*\[[ xX]\]\s*(.*)$", ac, re.M)
    items = [i for i in items if i.strip()]
    if not items:
        errs.append("Acceptance Criteria: no items")
    for n, item in enumerate(items, 1):
        m = re.match(r"AC-(\d+)\s+(.*)$", item)
        if not m:
            errs.append("AC line %d must start with 'AC-%d <text>': %r" % (n, n, item[:40]))
            continue
        if int(m.group(1)) != n:
            errs.append("AC numbering: expected AC-%d, found AC-%s" % (n, m.group(1)))
        if len(m.group(2).strip()) < 8:
            errs.append("AC-%d is too short to be testable" % n)
        v = VAGUE.search(m.group(2))
        if v:
            errs.append("AC-%d contains the vague word %r" % (n, v.group(0)))
    for line in sec.get("open questions", "").splitlines():
        if re.match(r"^\s*-\s*OP-\d+", line) and not re.search(r"\[(resolved|accepted by human)\b", line, re.I):
            errs.append("open question not closed (mark [resolved: ...] with a fact or the human's answer, or [accepted by human: ...]): %s" % line.strip()[:60])
    return errs


def template_block(path):
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(r"```markdown\n(.*?)\n```", text, re.S)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--issue")
    ap.add_argument("--sync-check", metavar="FILE", nargs="+")
    a = ap.parse_args()
    if a.sync_check:
        canon, bad = template_block(CANON), 0
        for f in a.sync_check:
            if template_block(f) != canon:
                print("FAIL: %s differs from references/spec-template.md" % f)
                bad = 1
        if not bad:
            print("PASS: template blocks match")
        return bad
    if a.issue:
        try:
            out = subprocess.check_output(["multica", "issue", "get", a.issue, "--output", "json"], text=True)
            text = json.loads(out).get("description") or ""
        except (OSError, subprocess.CalledProcessError, ValueError) as e:
            print("ERROR: cannot fetch %s: %s" % (a.issue, e))
            return 2
    elif a.file:
        text = sys.stdin.read() if a.file == "-" else Path(a.file).read_text(encoding="utf-8")
    else:
        ap.print_usage()
        return 2
    errs = check(text)
    for e in errs:
        print("FAIL: " + e)
    if not errs:
        print("PASS")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
