#!/usr/bin/env bash
# Copy third-party skills into skills/ UNCHANGED, so a result is attributable to them and not to our rewording.
# pstack: everything except `tdd`. Sources are pinned: mattpocock/skills 1.3.1 (plugin cache), pstack-claude @ 66181d3 (git clone). Both MIT.
#   tools/vendor-skills.sh <pstack-claude checkout>
set -euo pipefail
cd "$(dirname "$0")/.."
MP=${MATTPOCOCK:-$HOME/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.3.1/skills}
PS=${1:?path to a pstack-claude checkout (git rev-parse HEAD should be 66181d3...)}/plugins/pstack/skills
for s in engineering/tdd engineering/diagnosing-bugs engineering/codebase-design engineering/code-review \
         engineering/to-spec engineering/to-tickets engineering/pr engineering/retro engineering/domain-modeling \
         productivity/grilling; do
  rm -rf "skills/$(basename "$s")"; cp -r "$MP/$s" "skills/$(basename "$s")"
done
for d in "$PS"/*/; do
  s=$(basename "$d"); [ "$s" = tdd ] && continue   # name clashes with mattpocock's tdd; one workspace, one namespace
  rm -rf "skills/$s"; cp -r "$d" "skills/$s"
done
