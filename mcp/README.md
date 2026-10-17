One file per MCP server: `mcp/<name>.json` holds the server entry (the object that sits under a name in "mcpServers").
Reference it from an agent with `"mcp": ["<name>"]`. Files containing tokens should be gitignored (e.g. `mcp/*.local.json`).
