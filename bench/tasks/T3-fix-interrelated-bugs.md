# T3 — Diagnose and fix bugs from symptom reports

- **Repo**: `kv-bugs` (registered in the workspace; Forgejo `squadadmin/kv-bugs`). Baseline = tag `bench-base-t3` (= `main`, never merged into). Same code as `kv-cli` plus one seeded bug.
- **Ability under test**: diagnosis from symptoms (root cause not given), rework loop, reviewer catching an incomplete fix, not breaking existing tests.

## Requirement (give this text to the leader verbatim, in chat)
Users of `kv` report three problems. Find the causes and fix them; do not change any command's CLI surface.
1. `kv list` does not print keys in alphabetical order (e.g. `b` shows up before `aa`). Expected: plain byte-wise ascending key order.
2. After any `kv set` / `kv del`, the store file's permissions change (a 0644 or 0640 file becomes 0600), which locks out other users sharing it. Expected: permissions of an existing store file are preserved.
3. Running many `kv set` / `kv del` at the same time against one store file loses updates (keys written by some processes disappear, deleted keys come back). Expected: every successful concurrent write is reflected in the final store.
Add regression tests for each. Work on branch `fix/kv-bugs-<variant>-a<attempt>`; the final stage opens a PR against `main` with the forgejo-pr skill. **Do not merge the PR.**

## Seeded vs. natural bugs
Bug 1 is seeded (length-first comparator in `List`; the existing test uses equal-length keys so it stays green). Bugs 2 and 3 are natural weaknesses of the original `save()` (temp file from `os.CreateTemp` is 0600; read-modify-write without lock or reload).

## Why it should stress the squad
- Bug 3 has no one-line fix: it needs inter-process locking **and** reloading from disk under the lock, in both `Set` and `Delete`. A lock without reload still loses updates.
- The naive lock-file approach leaves a `.lock` file beside the store and breaks the existing `TestNoTempFilesLeft` / `TestSetFailureCleansTemp`; the squad must notice and resolve this consciously (lock elsewhere, or update those tests with justification).

## Hidden acceptance tests
`bench/hidden/T3/zz_hidden_t3_test.go` — black-box, builds the binary, drives it. Validated: on the baseline the order, permission, concurrent-set and concurrent set/delete tests fail; same-key and behaviour-regression tests pass; a reference implementation (flock + reload + mode preservation + bytewise sort) passes everything, stably over repeated runs. Tolerates a leftover `*.lock` file but not `*.tmp`.
Not specified, so not tested: where the lock lives, new-file permissions, Windows support.

## Keeping the record
Never delete branches, PRs, issues or labels from a scored run (same rules as T2).
