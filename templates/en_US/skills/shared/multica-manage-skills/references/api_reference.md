# multica API reference

Source: multica server routes and handler implementations (see the multica source repo).
Online address: `<MULTICA_API_URL>` (override via `MULTICA_API_URL` for intranet deployments).

## General conventions

- Authentication: `Authorization: Bearer <token>`; the token is a Personal Access Token (`mul_` prefix), created in UI Settings → Access Tokens. Note: this skill's scripts do not read local config files; token/address come only from the `--token`/`--url` flags or the environment variables `MULTICA_API_TOKEN`/`MULTICA_API_URL`.
- Workspace scope: request header `X-Workspace-Slug: <slug or UUID>`; the server resolves both (see `resolveWorkspaceID` in `middleware/auth.go`).
- CSRF: only state-changing requests made via cookie sessions need `X-CSRF-Token`; GET with a Bearer token needs no CSRF.
- Client headers (optional, sent by the frontend): `X-Client-OS: windows`, `X-Client-Platform: web`, `X-Client-Version: dev`, `X-Request-ID: <uuid>`.

## Endpoints

### User level (no workspace header needed)

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/me` | Current user info (id, email, name, etc.) |

### Requires the `X-Workspace-Slug` header

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/workspaces` | All workspaces visible to the current user (note: this is a global list and needs no slug header) |
| GET | `/api/agents` | Agent list within the workspace |
| GET | `/api/agent-run-counts` | 30-day run count per agent (RUNS column of the Agents list) |
| GET | `/api/agent-activity-30d` | 30-day daily activity per agent (data source of the ACTIVITY sparkline in the Agents list) |

## Response structure (confirmed from source)

### `GET /api/workspaces` → `WorkspaceResponse[]`

```json
[{
  "id": "uuid",
  "name": "My Workspace",
  "slug": "1",
  "description": null,
  "context": null,
  "settings": {},
  "repos": {},
  "issue_prefix": "MYT",
  "avatar_url": null,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}]
```

### `GET /api/agents` → `AgentResponse[]`

```json
[{
  "id": "uuid",
  "workspace_id": "uuid",
  "runtime_id": "uuid",
  "name": "support-agent",
  "description": "...",
  "instructions": "...",
  "runtime_mode": "issue | autopilot | chat",
  "custom_args": [],
  "archived_at": null,
  "created_at": "...",
  "updated_at": "..."
}]
```

### `GET /api/agent-run-counts` → `AgentRunCount[]`

```json
[{"agent_id": "uuid", "run_count": 20}]
```

### `GET /api/agent-activity-30d` → `AgentActivityBucket[]`

```json
[{"agent_id": "uuid", "bucket_at": "2026-08-23T00:00:00Z", "task_count": 5, "failed_count": 1}]
```

`bucket_at` is 00:00 UTC of that day; aggregated by day.

## Common errors

| Status | Meaning | Action |
| --- | --- | --- |
| 401 | Unauthenticated / invalid token | Replace the token (`--token` flag or `MULTICA_API_TOKEN` env var) |
| 403 | Insufficient permission / not a workspace member | Confirm the token owner belongs to that workspace |
| 404 | Workspace does not exist | Use the `workspaces` subcommand to confirm the slug |
| 502/504 | Service not ready | Check service status (nginx reverse proxy 80 → backend) |

