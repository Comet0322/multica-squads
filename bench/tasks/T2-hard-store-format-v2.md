# T2-hard — Add a versioned store format with backward-compatible migration

- **Repo**: `kv-cli` (registered in the workspace; Forgejo `squadadmin/kv-cli`). Baseline = git tag `bench-base-t2` (= `main`, never merged into). Base branch for the PR stays `main`.
- **Scenario / scope tier**: scenario 2 (add a feature to an existing repo), tier A (scored, pass^3).
- **Ability under test**: a feature whose difficulty is in the *edge cases implied by the requirement*, not in the amount of code. It replaces T2, which 3 runs passed with zero rework and therefore exercised neither review nor QA.

## Requirement (give this text to the leader verbatim, in chat)
`kv` stores everything in a bare JSON object, so the file format can never change. Introduce a versioned format.

1. The new format (v2) is a JSON object `{"version":2,"data":{"<key>":"<value>", ...}}`, where `version` is the JSON number 2 and `data` maps string keys to string values.
2. `kv set` and `kv del` always write v2.
3. A v1 file (a bare `{"key":"value"}` object) must still be readable. The first time a v1 file is written to, it is migrated to v2 and a copy of the original file is kept next to it as `<store>.v1.bak`. If a `<store>.v1.bak` already exists, leave it exactly as it is and still migrate.
4. A new store file (no file yet) is created directly in v2, with no `.bak`.
5. `kv get` and `kv list` must never modify the store file and never create any file, whatever the format.
6. Migrating an existing file preserves that file's permissions: a 0644 store file is still 0644 afterwards.
7. New command `kv version`: prints `1` or `2`, the format of the current store file, and exits 0. With no store file yet it prints `2`. It takes no arguments; wrong usage exits 2 like the other commands.
8. Everything else is unchanged: the output and exit codes of `set`, `get`, `del` and `list`; an unreadable or malformed store file is still an error with a message on stderr and exit 1 (a value that is not a string is malformed, in either format); an empty file is still an empty store.
9. README documents the format, the migration and the new command.

Work on branch `feat/kv-format-v2-<variant>-a<attempt>` (e.g. `feat/kv-format-v2-v6-a1`); the final stage opens a PR against `main` with the forgejo-pr skill. **Do not merge the PR** (the scorer reads the branch; `main` must stay at the baseline so every attempt starts identically).

## Expected touched files
`main.go`, `internal/kvstore/*` (format handling + tests), `README.md`. Anything else is out of scope.

## Why it should stress the squad
The code is small; the thinking is not. The requirement implies five things it never spells out:
- **Format detection is ambiguous.** A v1 store may legitimately contain keys called `version` and `data` — `{"version":"2","data":"hello","a":"1"}` is a valid v1 file with three keys. Detecting v2 by "has a `version` field" silently destroys it. The decisive difference is types: in v1 every value is a string, so only a *numeric* `version` with an *object* `data` is v2.
- **Read-only must mean read-only.** The natural implementation (load, normalise, save) would rewrite the file on `get`, which breaks a read-only directory and a shared file.
- **Permission preservation** cannot be had from `os.CreateTemp` + rename, which is what `save()` does today (the temp file is 0600).
- **The backup is once, not per write**, and must never clobber an existing `.bak`.
- **Atomicity still applies**: no `.tmp` files left behind, and the existing `TestNoTempFilesLeft` / `TestSetFailureCleansTemp` must stay green.

## Hidden acceptance tests
`bench/hidden/T2-hard/zz_hidden_t2hard_test.go` — black-box (builds the binary, drives it via `KV_FILE`), so it does not depend on internals.
Covers: `version` on a missing store; reading a v1 file without touching it (bytes, mode and mtime unchanged, no file created); first write migrates and leaves an exact `.v1.bak`; an existing `.bak` is not overwritten; the ambiguous `version`/`data` v1 file survives a write with all keys intact; mode preserved across migration; the second write stays v2 with no second backup; a v2 round trip with unicode, `=`, newlines and empty values; and a regression block for every existing command, exit code, malformed-file and empty-file behaviour.
Validated before use: on the baseline (`bench-base-t2`) the nine feature tests fail and the four behaviour/regression tests pass, with the repo's existing tests green; a reference implementation (envelope + type-based detection + once-only `.v1.bak` + chmod-before-rename + a read-only `Version()`) passes all thirteen, three runs in a row, with `go build`, `go vet` and `gofmt` clean. The reference implementation is kept outside this repo so it cannot leak into a run.
Not specified by the requirement, so deliberately not tested: the permissions of the `.bak` and of a newly created store, the format version reported for an empty file, extra unknown top-level fields in a v2 file, and concurrent writes (that is T3's subject).

## Keeping the record
Never delete branches, PRs, issues or labels from a scored run. Each attempt has its own branch, PR, spec issue and run label, so every attempt stays inspectable. Attempts do not interfere because they all branch from the unmoved `main`.
