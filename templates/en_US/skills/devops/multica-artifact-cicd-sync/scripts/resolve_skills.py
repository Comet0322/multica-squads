"""Resolve platform skill directories for orchestrator scripts.

Priority: MULTICA_SKILLS_ROOT > sibling of the caller skill directory.
"""
from __future__ import annotations

import os
from pathlib import Path


def resolve_skill_dir(skill_name: str, caller_skill_dir: Path | str | None = None) -> Path:
    root = os.environ.get("MULTICA_SKILLS_ROOT")
    if root and (Path(root) / skill_name).is_dir():
        return Path(root) / skill_name
    if caller_skill_dir:
        sibling = Path(caller_skill_dir).resolve().parent / skill_name
        if sibling.is_dir():
            return sibling
    raise FileNotFoundError(
        f"cannot locate skill '{skill_name}'. Set MULTICA_SKILLS_ROOT or co-locate skills under templates/skills/."
    )


__all__ = ["resolve_skill_dir"]
