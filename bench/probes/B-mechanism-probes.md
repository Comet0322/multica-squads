# B-layer probes — mechanisms that must work, verified once

Tier B scenarios are not scored repeatedly: each needs one demonstration that the
mechanism exists and works. These runs are real squad runs (they cost agent time), but
they are not scored runs and do not count against the budget in `rubric.json`.

## B1 — greenfield, with the mid-run change request riding along (scenarios 1 + 10)
One small new CLI in an empty repo, run hands-off from chat to open PR.

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
cover.

Pass conditions:
1. The leader says it looks tiny and asks the single yes/no question before starting.
2. On yes: a spec issue with handoff children only — implement, review, open PR — and
   no ticket level, no spec check, no QA, no docs.
3. On anything other than an explicit yes: the normal flow.
4. A request failing any of the four tests is NOT offered the fast path. Checked with
   one negative case in the same session (two files, or a new behaviour).
