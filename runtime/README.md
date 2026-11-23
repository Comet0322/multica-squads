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
