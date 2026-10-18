#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Load authentication environment variables: prefer the local Windows system / process environment variables.

Priority (high -> low):
  1) OS environment variables (User / Machine / already in the process)
  2) Optional local files (only fill gaps; never override system variables):
       <skill>/config.local.env
       <skill>/.env.local
       <skill>/.env

Rules:
  - By default, do not store real credentials in the Skill directory; configure them as system environment variables
  - If a local file exists, its keys are written only when the matching environment variable is empty
  - Never commit a config.local.env that contains real passwords
"""
from __future__ import annotations

import os
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_CANDIDATES = (
    _SKILL_ROOT / "config.local.env",
    _SKILL_ROOT / ".env.local",
    _SKILL_ROOT / ".env",
)

_LOADED_FROM: str | None = None
_SYSTEM_ENV_MERGED = False

# Authentication-related keys the scripts care about (merged from Windows User/Machine environment into the current process)
_AUTH_KEYS = (
    "JIRA_USERNAME",
    "JIRA_PASSWORD",
    "JIRA_USERNAME",
    "JIRA_PASSWORD",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_COOKIE",
    "CONFLUENCE_COOKIE",
    "FIGMA_TOKEN",
    "TEAM_KB_URL",
    "TEAM_KB_TIMEOUT",
)


def skill_root() -> Path:
    return _SKILL_ROOT


def _merge_windows_system_env() -> None:
    """Merge local User/Machine-level system variables into os.environ (never overriding non-empty values already in the process)."""
    global _SYSTEM_ENV_MERGED
    if _SYSTEM_ENV_MERGED:
        return
    _SYSTEM_ENV_MERGED = True
    if os.name != "nt":
        return
    try:
        import winreg
    except ImportError:
        return

    roots = (
        (winreg.HKEY_CURRENT_USER, r"Environment"),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
    )
    for hive, subkey in roots:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                    except OSError:
                        break
                    i += 1
                    if name not in _AUTH_KEYS:
                        continue
                    if value is None:
                        continue
                    text = str(value).strip()
                    if not text:
                        continue
                    if not os.environ.get(name, "").strip():
                        os.environ[name] = text
        except OSError:
            continue


def _parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    text = path.read_text(encoding="utf-8-sig")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        data[key] = value
    return data


def load_local_env(prefer_local: bool = False) -> str | None:
    """Merge system environment variables, optionally filling gaps from a local file.

    Args:
        prefer_local: When False (default), system/process environment variables win and the local file only fills gaps;
            when True, the local file overrides existing variables of the same name (not recommended).

    Returns:
        Path string of the local file actually loaded; None if no local file was used.
    """
    global _LOADED_FROM
    _merge_windows_system_env()

    chosen: Path | None = None
    for path in _CANDIDATES:
        if path.is_file():
            chosen = path
            break
    if chosen is None:
        return None

    parsed = _parse_env_file(chosen)
    for key, value in parsed.items():
        if prefer_local or key not in os.environ or os.environ.get(key, "") == "":
            os.environ[key] = value
    _LOADED_FROM = str(chosen)
    return _LOADED_FROM


def ensure_local_env(prefer_local: bool = False) -> str | None:
    """Idempotent load: repeated calls parse only once; the system environment is merged every time."""
    _merge_windows_system_env()
    if _LOADED_FROM:
        return _LOADED_FROM
    return load_local_env(prefer_local=prefer_local)


# Load on import so each script needs only a single import line
ensure_local_env()
