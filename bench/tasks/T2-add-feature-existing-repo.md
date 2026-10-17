# T2 — Add a feature to an existing repo

- **Repo**: `kv-cli` (registered in the workspace; Forgejo `squadadmin/kv-cli`). Baseline = git tag `bench-base-t2` (equal to `main` now). Base branch for the PR stays `main`.
- **Ability under test**: leader reads the real repo before writing the spec; change stays in scope; existing behavior is not broken.

## Requirement (give this text to the leader verbatim, in chat)
Add `kv export` and `kv import`:
- `kv export` prints the whole store as one JSON object `{"key":"value",...}` to stdout, keys sorted, exit 0. Empty store prints `{}`.
- `kv import` reads a JSON object from stdin and sets every key (overwriting existing keys, keeping others). Invalid JSON or non-string values: stderr error, exit 1, store unchanged (all-or-nothing).
- Existing commands and their exit codes must not change. README documents both commands.
- Work on branch `feat/kv-export-import-<variant>-a<attempt>` (e.g. `feat/kv-export-import-v1-a1`); the final stage opens a PR against `main` with the forgejo-pr skill. **Do not merge the PR** (the scorer reads the branch; `main` must stay at the baseline so every attempt starts identically).

## Expected touched files
`main.go`, `internal/kvstore/*` (new method(s) + tests), `README.md`. Anything else is out of scope.

## Hidden acceptance tests
`bench/hidden/T2/zz_hidden_t2_test.go` — black-box (builds the binary, drives it via `KV_FILE`), so it does not depend on how the squad structures internals. Covers: export of empty store (`{}`), content + sorted keys, special characters round trip, import merge/overwrite, import `{}` no-op, import rejected atomically (invalid JSON, non-object, number/null/nested values, empty stdin, trailing garbage; exit 1, stderr set, store unchanged), and regression of existing commands/exit codes.
Validated: on unmodified `main` all new tests fail and the regression test passes; a reference implementation passes all. Note `null` values are a deliberate trap (Go's json decodes null into a string silently).
Not specified by the requirement, so deliberately not tested: extra args to `export`/`import`, output whitespace.

## Keeping the record
Never delete branches, PRs, issues or labels from a scored run. Each attempt has its own branch, PR, parent issue and run label, so every attempt stays inspectable. Attempts do not interfere because they all branch from the unmoved `main`.
