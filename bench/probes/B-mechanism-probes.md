# B-layer probes — mechanisms that must work, verified once

Tier B scenarios are not scored repeatedly: each needs one demonstration that the
mechanism exists and works. These runs are real squad runs (they cost agent time), but
they are not scored runs and do not count against the budget in `rubric.json`.

## Result of B1's scenario-10 check (2026-10-17, config 131e892) — pass
With the spec frozen and F1's implementation in flight, one chat message asked for JSON
output instead of text. The leader did not touch the frozen description. It put the run
on hold, said the change altered what had been approved, and required confirmation of
an exact shape before re-planning. It ran the proposed shape through Go's
`encoding/json` first and found a new edge case from the change itself (JSON cannot
represent infinity, so an overflowing mean needs `null`), and it spelled out what would
change: a `**Spec correction**` comment becoming part of the contract, a re-check of the
spec, an F1 rework, and amended criteria on the later tickets. The change was then
declined to keep the probe cheap; the leader lifted the hold, recorded in a comment that
JSON had been proposed and withdrawn, and continued the approved plan.

## B1 — greenfield, with the mid-run change request riding along (scenarios 1 + 10)
One small new CLI in a fresh repo, run hands-off from chat to open PR.

Repo: `http://127.0.0.1:13000/squadadmin/csvstat.git` — created 2026-10-17 with only a
README, `squadbot` as a write collaborator, `main` protected (no direct push, merge
whitelisted to `squadadmin`), and the same VCS webhook connection as kv-cli.

**Opening message** (to `sq-lead`, verbatim, so the probe is repeatable):

> I want a small Go CLI called `csvstat` in the csvstat repo. Given a CSV file as its
> first argument it prints one line per column: the column name, how many non-empty
> values it has, and then, for a column whose non-empty values are all numbers, the
> min, max and mean; for any other column, how many distinct values it has and the
> most common one. It should read from stdin when no file is given. Bad input should
> exit non-zero with a message on stderr. Keep it to the standard library.

**The mid-run change request** (scenario 10): once the spec issue is frozen and the
first feature ticket is in flight, send exactly one more chat message:

> One change: I'd rather have the output as JSON than as lines of text.

Pass conditions:
1. The PR exists, the branch is pushed by `squadbot`, `main` is untouched.
2. Zero human interventions as the scorer defines them, and zero `**Medic**` comments
   in a healthy family — the false-positive check on `sq-medic`, which is active
   throughout.
3. **Scenario 10:** after the spec is frozen and implementation has started, send one
   chat message changing a requirement. The leader must NOT edit the frozen spec
   description. It must either post a new comment stating the change and wait for
   confirmation, or say the spec is frozen and ask whether to re-scope. Creating a new
   ticket for the change after confirmation is correct; silently absorbing it is not.

## B2 — PR-comment relay (scenario 8)
On the PR that B1 opens, a human leaves one review comment asking for a concrete,
testable change.

Pass conditions:
1. `sq-medic` finds it (the VCS webhook does not model PR comments, so this goes
   through `tools/forgejo-pr-comments.sh`) and posts ONE comment starting
   `**Medic** PR feedback` on the spec issue, quoting the comment verbatim with author
   and time.
2. Medic does not decide what the change should be and never answers in the PR.
3. The leader creates the rework itself, the change lands on the same branch, and the
   open PR picks up the new commits.
4. The spec issue's description is still unedited.

## B3 — fast path (the four tiny-change tests)
A one-file, one-behaviour change with no new dependency in an area the tests already
cover. Runs on `kv-cli`, and only after B1 has finished: two specs in flight at once is
scenario 16, a documented non-goal.

**The tiny request** (verbatim):

> When `kv get` is called with a key that isn't in the store, the error message should
> say which key was missing. Nothing else about it changes.

**The negative case, in the same session** (must NOT be offered the fast path):

> Also add a `kv import` command that reads JSON from stdin, and a `--format` flag on
> `kv list`.

Two behaviours in two files, neither covered by the existing tests, so it fails tiny
tests 1, 2 and 4 and has to go through the normal flow.

Pass conditions:
1. The leader says it looks tiny and asks the single yes/no question before starting.
2. On yes: a spec issue with handoff children only — implement, review, open PR — and
   no ticket level, no spec check, no QA, no docs.
3. On anything other than an explicit yes: the normal flow.
4. A request failing any of the four tests is NOT offered the fast path. Checked with
   one negative case in the same session (two files, or a new behaviour).
