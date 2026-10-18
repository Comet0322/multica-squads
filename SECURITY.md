# Security Policy

## When sharing this repo or your configs

When publishing templates, screenshots, or derived configs:

### Never include

- API keys, tokens, cookies, private keys
- Local absolute paths (`/Users/...`, `C:\...`)
- Real workspace names, slugs, or internal URLs
- Real emails or account names
- Production credentials or MCP configs with secrets

### Always

- Replace secrets with placeholders (`YOUR_API_KEY`, `<workspace-slug>`)
- Review every file before each `git push`
- Keep credentials in environment variables and Multica runtime config, never paste them into Instructions

## High-privilege Skills

Skills that control browsers, mouse, Shell, or deploys should:

- Be mounted only to agents that actually need them
- Be human-reviewed before first use in a shared workspace
- Declare explicit boundaries in the Agent Instructions

## Reporting security issues

If you find a security-sensitive mistake in this repo (e.g. an accidental secret in an example), report it through a private channel, or open an Issue without pasting the secret and, if needed, ask for git history cleanup.

## Agent behavior

AI agents are non-deterministic. Human gates are required before high-risk actions such as destructive file operations, production deploys, and external publishing — see [`docs/en_US/gates-and-evidence.md`](docs/en_US/gates-and-evidence.md).
