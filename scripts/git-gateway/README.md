# Git gateway (MCP)

Lets coding agents clone / push / open MRs without ever holding a git credential. FastMCP server, streamable HTTP on `127.0.0.1:8930/mcp`.

Tools: `git_clone`, `git_push`, `open_mr`, `mr_status`, `list_branches`.

## Run

```bash
cp config.example.json config.local.json      # edit allowed_root, repos
echo "WORKSPACES_ROOT=$HOME/multica_workspaces" > .env
docker volume create gw-secrets
printf '%s' "$GIT_HOST_TOKEN" | docker run --rm -i -v gw-secrets:/s python:3.12-slim sh -c 'cat > /s/token && chmod 600 /s/token'
docker compose up -d --build
```

Point agents at it with `"mcp_config": {"mcpServers": {"git": {"type": "http", "url": "http://127.0.0.1:8930/mcp"}}}` (no credential in it).

## Guarantees and limits

- Token is read from a root-owned Docker volume; it is not in env, argv, a stored remote URL, or tool output (outputs are scrubbed).
- `git_push` fetches the branch into a gateway-owned bare repo and pushes from there, so agent-writable hooks/config never run in the gateway.
- Only allowlisted repos, only `branch_prefix` branches, never the default branch, no force, MR is opened but never merged.
- Audit log: `/var/lib/gw/audit.log` in the `gw-data` volume.
- Not a sandbox: anything that can use the Docker socket (the `docker` group) can still read the volume. The port is also usable by any local process.

## Deployment constraint (Kubernetes)

The runtime pod must never hold a git credential. Run the gateway as a sidecar:

- The token is mounted as a Secret into the **sidecar container only** (not the runtime container, not the pod's shared env).
- The runtime reaches the sidecar over `127.0.0.1` (same pod network namespace) and has no route or credential to the git host; use a NetworkPolicy to deny runtime egress to it if the sidecar is the only path.
- The agent workspace root is a volume shared by both containers (`emptyDir`/PVC) mounted at the **same path** in each; `allowed_root` in the gateway config is that path.
- Clone, push, read and MR go only through the gateway tools. Do not enable Multica's own `multica repo checkout` for this git host and keep the workspace repo list free of it: it relies on the daemon's git credentials.
- Skills and agent prompts must not assume the runtime can obtain a token (no `*_TOKEN` env var, no credential helper, no `~/.git-credentials`). `multica-platform-git-host` is the exception that does assume a PR-only token in the env; do not attach it to agents in this deployment.
