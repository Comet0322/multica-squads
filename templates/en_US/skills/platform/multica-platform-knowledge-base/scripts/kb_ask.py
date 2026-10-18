#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ask Wiki knowledge-base questions through the Knowledge Base Bridge (stdlib only, cross-platform)."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BRIDGE = "http://kb-bridge.example.com:3910"
MIN_TASK_ID = 500_000_000


def _bridge_url() -> str:
    return os.environ.get("KB_BRIDGE", DEFAULT_BRIDGE).rstrip("/")


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def http_json(method: str, url: str, body: dict | None = None, timeout: int = 60) -> dict:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot connect to Bridge ({url}): {exc.reason}. "
            f"Make sure {DEFAULT_BRIDGE} is reachable on the intranet, and set KB_BRIDGE if needed."
        ) from exc


def build_prompt(question: str, system_code: str) -> str:
    # Functional: the bridge matches this exact Chinese prefix ("Wiki knowledge-base Q&A"); do not translate.
    prompt = "【Wiki 知识库问答】"
    if system_code and system_code.upper() != "ALL":
        prompt += f"系统：{system_code}。"  # "系统" = "System"; part of the bridge prompt format
    prompt += question.strip()
    return prompt


def check_health(bridge: str | None = None, verbose: bool = True) -> dict:
    base = (bridge or _bridge_url()).rstrip("/")
    health = http_json("GET", f"{base}/health")
    if not health.get("ok"):
        raise RuntimeError(f"Bridge health check failed: {json.dumps(health, ensure_ascii=False)}")
    if verbose:
        print(
            f"bridge=ok cwd={health.get('cwd')} node={health.get('node')}",
            file=sys.stderr,
        )
    return health


def ask(
    question: str,
    system_code: str = "ALL",
    *,
    bridge: str | None = None,
    task_id: int | None = None,
    poll_interval: int | None = None,
    poll_timeout: int | None = None,
    verbose: bool = True,
) -> dict:
    base = (bridge or _bridge_url()).rstrip("/")
    poll_interval = poll_interval if poll_interval is not None else _env_int("KB_POLL_INTERVAL", 2)
    poll_timeout = poll_timeout if poll_timeout is not None else _env_int("KB_POLL_TIMEOUT", 600)
    task_id = task_id if task_id is not None else int(
        os.environ.get("KB_TASK_ID") or (MIN_TASK_ID + random.randint(0, 999_999))
    )
    if task_id < MIN_TASK_ID:
        raise ValueError(f"taskId must be >= {MIN_TASK_ID}, got {task_id}")

    check_health(base, verbose=verbose)

    output_dir = f"/tmp/cursor_kb_qa/{task_id}"
    http_json(
        "POST",
        f"{base}/v1/sessions",
        {"taskId": task_id, "outputDir": output_dir},
    )

    prompt = build_prompt(question, system_code)
    run_resp = http_json(
        "POST",
        f"{base}/v1/sessions/{task_id}/runs",
        {"prompt": prompt},
    )
    run_id = run_resp.get("runId")
    if not run_id:
        raise RuntimeError(f"No runId returned: {json.dumps(run_resp, ensure_ascii=False)}")

    if verbose:
        print(f"runId={run_id} taskId={task_id}", file=sys.stderr)

    elapsed = 0
    while elapsed < poll_timeout:
        time.sleep(poll_interval)
        elapsed += poll_interval
        run = http_json("GET", f"{base}/v1/runs/{run_id}")
        status = run.get("status")
        if verbose:
            print(f"status={status} elapsed={elapsed}s", file=sys.stderr)

        if status == "finished":
            answer = run.get("streamingText") or run.get("result") or ""
            if isinstance(answer, dict):
                answer = json.dumps(answer, ensure_ascii=False, indent=2)
            return {
                "bridge": base,
                "taskId": task_id,
                "runId": run_id,
                "status": status,
                "prompt": prompt,
                "answer": str(answer),
                "error": run.get("error"),
            }

        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(json.dumps(run, ensure_ascii=False))

    raise RuntimeError(f"Polling timed out ({poll_timeout}s), runId={run_id}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Knowledge Base Bridge Wiki Q&A")
    parser.add_argument("question", nargs="?", help="user question")
    parser.add_argument(
        "system_code",
        nargs="?",
        default="ALL",
        help="system code (CRM/MES/...), default ALL",
    )
    parser.add_argument("--health", action="store_true", help="run only the step 1 health check")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    parser.add_argument("-q", "--quiet", action="store_true", help="do not print progress to stderr")
    args = parser.parse_args()

    verbose = not args.quiet
    try:
        if args.health:
            health = check_health(verbose=verbose)
            if args.json:
                print(json.dumps(health, ensure_ascii=False, indent=2))
            else:
                print(json.dumps(health, ensure_ascii=False))
            return 0

        if not args.question:
            parser.error("missing question; use --health for a health check only")

        result = ask(args.question, args.system_code, verbose=verbose)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["answer"])
        return 0
    except Exception as exc:  # noqa: BLE001 — single CLI error exit
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
