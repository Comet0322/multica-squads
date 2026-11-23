# squads-runtime — isolated agent runtime

A container that runs the Multica daemon, so every agent run executes here, not on the host.
Contains Claude Code, Go, Node 22, Python 3, gh, git, build tools, and the Multica CLI pinned to **v0.11.0**.

- Joins `multica-selfhost_default`; the daemon talks to `http://backend:8080` directly.
- `.env` (gitignored, mode 600) holds `MULTICA_TOKEN`. `entrypoint.sh` writes it to the container's
  `~/.multica/config.json` at start; it is not in the image.
- Commits default to `squad-runtime <squad-runtime@multica.local>`, never a person's address.
- Volumes: `claude-home` (Claude login), `workspaces` (run checkouts), `multica-home`.

```bash
docker compose up -d --build                 # start / rebuild
docker exec -it squads-runtime claude        # one-time Claude login (persists in claude-home)
docker exec -it squads-runtime gh auth login # when agents must push / open PRs
docker compose logs -f / docker exec squads-runtime multica daemon status
SQUADS_RUNTIME_NAME=squads-runtime ../sync.py   # bind agents to this runtime
```
Optional in `.env`: `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`), `GH_TOKEN`.
Do not run a host daemon at the same time: agents bind to one runtime.

## Selfhost server (outside this repo)
The server this runtime connects to lives in `~/multica-selfhost` (not a git repo; `.env` holds secrets), so its state is recorded here.
- Upgraded in place from v0.8.1 to **v0.11.0** on 2026-11-23 via `MULTICA_IMAGE_TAG`; the DB backup is `~/multica-selfhost/backups/pre-v0.11.0-20261123-2002.sql.gz`. Migrations are one-way.
- **Always pass `-p multica-selfhost`**: `docker compose -p multica-selfhost -f docker-compose.selfhost.yml ...`. Without it compose picks project `multica`, creates duplicate containers and fails on the port.
- No email backend is configured, so login codes are not mailed. `.env` sets `MULTICA_DEV_VERIFICATION_CODE=888888` and `APP_ENV=development` (the fixed code is ignored when `APP_ENV=production`), and `docker-compose.selfhost.yml` passes the variable to `backend`. Any email logs in with `888888`; the port is bound to 127.0.0.1 only. A first login creates the account, so delete probe accounts you create while testing.
- Host CLI: `~/.local/bin/multica` is a v0.11.0 build from tag `v0.11.0` (the brew 0.12.0 is shadowed). Do not run a host `multica daemon` while this container runs.
