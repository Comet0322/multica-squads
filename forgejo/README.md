# Local Forgejo for Multica

- `docker compose up -d` (needs `.env` with FORGEJO_ADMIN_USER; gitignored). Admin password and the merge-capable API token live in `.env.admin`, which nothing the squad runs ever sources — the squad only ever holds `FORGEJO_TOKEN` (squadbot, cannot merge).
- UI: http://localhost:13000, joined to the `multica_default` network so the Multica backend reaches it as `http://forgejo:3000`.
- Connect: POST /api/workspaces/{id}/vcs/connections {provider: forgejo, instance_url: http://forgejo:3000, access_token}.
- Per repo webhook target must be the in-network URL `http://backend:8080/api/webhooks/vcs/<connection-id>` (the UI shows localhost, which Forgejo cannot reach). Events: pull_request, status. Secret = connection's webhook_secret (shown once).
- A merged PR whose body says `Closes <ISSUE-ID>` moves the issue to done.
