---
name: multica-manage-skills
description: "Query the deployed multica platform API for workspace / agent statistics (agent run counts, 30-day activity breakdown, per-workspace summaries). Use when the user needs multica data (for example \"agent run counts per workspace\", \"workspace statistics\", \"multica API data\") or needs to access the API at <MULTICA_API_URL>. The script is pure standard-library Python; no dependencies to install."
---

# multica-manage-skills

## Overview

multica is a self-hosted agent orchestration platform (online address `<MULTICA_API_URL>`). This skill provides a Python API client that can be called at any time to fetch the workspace list, the agent list of each workspace, each agent's 30-day run count and daily activity breakdown, and to print summary reports.

## Authentication and configuration

The script authenticates with `Authorization: Bearer <token>`; the workspace is specified through the `X-Workspace-Slug` request header (slug or UUID both work).

**The script reads no local configuration file** (it does not read `~/.multica/config.json`, nor any json in the script directory). It accepts only command-line arguments and environment variables, so that files on the local disk cannot interfere.

Token resolution priority (high to low):
1. `--token` argument
2. Environment variable `MULTICA_API_TOKEN`

API address resolution priority (high to low):
1. `--url` argument
2. Environment variable `MULTICA_API_URL`
3. Default `<MULTICA_API_URL>`

> Recommended: put the token and address into environment variables once and for all (PowerShell persistent example):
> ```powershell
> [Environment]::SetEnvironmentVariable("MULTICA_API_TOKEN", "mul_xxx", "User")
> [Environment]::SetEnvironmentVariable("MULTICA_API_URL", "<MULTICA_API_URL>", "User")
> ```
> Takes effect in newly opened terminals. Create the token in the Web UI under Settings → Access Tokens (shaped like `mul_xxx`). If the script reports 401/403, check `MULTICA_API_TOKEN` first.

## Quick start

Script location: `{skill_base_dir}/scripts/multica_api.py` (user-level skill, usable from any project).

```powershell
# List all workspaces
python scripts/multica_api.py workspaces

# Agent list of a workspace
python scripts/multica_api.py agents --workspace <workspace-slug>

# 30-day run count of every agent in a workspace (JSON output)
python scripts/multica_api.py run-counts --workspace <workspace-slug> --json

# 30-day daily activity of every agent in a workspace
python scripts/multica_api.py activity --workspace <workspace-slug>

# Summary statistics for all workspaces
python scripts/multica_api.py report

# Agent-level detail of a single workspace (run counts + activity + names merged)
python scripts/multica_api.py report --workspace <workspace-slug>

# Specify token / address / CSV output
python scripts/multica_api.py --token YOUR_API_TOKEN --url <MULTICA_API_URL> report --csv
```

## Command overview

| Subcommand | Description | Required arguments |
| --- | --- | --- |
| `me` | Information about the currently logged-in user | none |
| `workspaces` | All workspaces visible to the current user (id/name/slug/created_at) | none |
| `agents` | Agent list of a workspace (id/name/runtime_mode) | `--workspace` |
| `run-counts` | 30-day run count of every agent in a workspace `[{agent_id, run_count}]` | `--workspace` |
| `activity` | 30-day daily activity of every agent in a workspace `[{agent_id, bucket_at, task_count, failed_count}]` | `--workspace` |
| `report` | Summary: without `--workspace`, prints a summary per workspace; with `--workspace`, prints the agent detail of that workspace (including fail_rate) | optional `--workspace` |

Common arguments: `--url`, `--token`, `--workspace`, `--json`, `--csv`.

## Common scenarios

1. **"Count the agent runs of each workspace"** → run `report` (without `--workspace`): one row per workspace, with agent count, total 30-day runs, task count and failure count.
2. **"How has a given agent run recently"** → `run-counts --workspace <ws>` for run counts, then `activity --workspace <ws>` for the daily breakdown; use `--json` for programmatic handling.
3. **Integrating as a Python module** → `from multica_api import MulticaClient`; after constructing `MulticaClient(base_url, token)`, call methods such as `list_workspaces()` / `agent_run_counts(ws)` / `workspace_report(ws)` directly. Errors are uniformly raised as `MulticaError`.
4. **Server unreachable / authentication failed** → the script prints the HTTP status code and a snippet of the response body; on 401/403 it prompts you to check the token.

## Endpoints (details in references/api_reference.md)

- `GET /api/me` and `GET /api/workspaces` need no workspace header
- `GET /api/agents`, `GET /api/agent-run-counts` and `GET /api/agent-activity-30d` require `X-Workspace-Slug`

## Resources

- `scripts/multica_api.py` — the API client + CLI described above (pure standard library; run directly or import)
- `references/api_reference.md` — endpoints, request headers and response structures (taken from the multica source)
