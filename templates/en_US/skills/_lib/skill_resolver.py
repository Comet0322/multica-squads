"""Shared helper: locate a sibling platform skill directory.

Used by orchestration / tester scripts that call scripts of platform skills.
Priority: MULTICA_SKILLS_ROOT > sibling of the caller skill's parent directory.
"""
from __future__ import annotations

import os
from pathlib import Path


def resolve_skill_dir(skill_name: str, caller_skill_dir: Path | str | None = None) -> Path:
    root = os.environ.get("MULTICA_SKILLS_ROOT")
    if root:
        for base in (Path(root), *Path(root).glob("*")):
            if (base / skill_name / "SKILL.md").is_file():
                return base / skill_name
    if caller_skill_dir:
        skills_root = Path(caller_skill_dir).resolve().parent.parent
        for candidate in (Path(caller_skill_dir).resolve().parent / skill_name,
                          *skills_root.glob(f"*/{skill_name}")):
            if candidate.is_dir():
                return candidate
    raise FileNotFoundError(
        f"cannot locate skill '{skill_name}'. Set MULTICA_SKILLS_ROOT or keep skills grouped under templates/en_US/skills/<role>/."
    )


__all__ = ["resolve_skill_dir"]
