# T2 — Add a feature to an existing repo

- **Repo**: `kv-cli` (registered in the workspace; Forgejo `squadadmin/kv-cli`, base branch `main` at the state after run 4).
- **Ability under test**: leader reads the real repo before writing the spec; change stays in scope; existing behavior is not broken.

## Requirement (give this text to the leader verbatim, in chat)
Add `kv export` and `kv import`:
- `kv export` prints the whole store as one JSON object `{"key":"value",...}` to stdout, keys sorted, exit 0. Empty store prints `{}`.
- `kv import` reads a JSON object from stdin and sets every key (overwriting existing keys, keeping others). Invalid JSON or non-string values: stderr error, exit 1, store unchanged (all-or-nothing).
- Existing commands and their exit codes must not change. README documents both commands.
- Work on branch `feat/kv-export-import`; final stage opens a PR with the forgejo-pr skill.

## Expected touched files
`main.go`, `internal/kvstore/*` (new method(s) + tests), `README.md`. Anything else is out of scope.

## Hidden acceptance tests
`bench/hidden/T2/` (to be written and reviewed before first scored run).
