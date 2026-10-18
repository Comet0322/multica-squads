#!/bin/bash
# Shared helper: resolve_skill_dir <skill-name> [caller-skill-dir]
# Priority: MULTICA_SKILLS_ROOT > any role directory next to the caller skill.
resolve_skill_dir() {
  local name="$1" caller="${2:-}" root="${MULTICA_SKILLS_ROOT:-}" hit
  if [ -n "$root" ]; then
    for hit in "$root/$name" "$root"/*/"$name"; do
      [ -f "$hit/SKILL.md" ] && { echo "$hit"; return 0; }
    done
  fi
  if [ -n "$caller" ]; then
    local skills_root
    skills_root="$(cd "$caller/../.." && pwd)"
    for hit in "$skills_root"/*/"$name"; do
      [ -d "$hit" ] && { echo "$hit"; return 0; }
    done
  fi
  echo "cannot locate skill '$name'. Set MULTICA_SKILLS_ROOT or keep skills grouped under templates/en_US/skills/<role>/." >&2
  return 1
}
