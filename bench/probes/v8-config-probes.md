# v8 config probes — the gate ADR 0002 set, all four passed

Date: 2026-10-18. Config `62bbc3c`. Deterministic probes, not scored runs: the fault is
injected by a human and the outcome does not depend on chance. Nothing was deleted; the
three probe branches and two PRs are left open on `kv-cli`, and `main` is untouched at
`c37bfe10092c2e8c7382d98a8c746a791d562318`.

| # | Claim | Probe | Result |
|---|---|---|---|
| 1 | A promotion out of `backlog` starts a run on the assignee | P1 | **PASS** |
| 2 | A `child_done` barrier wakes the ticket's owner, not the leader | P1 | **PASS** — 8 runs, only 1 on the leader |
| 3 | A stage reopened with two writes runs again, and the owner promotes the right stage | P2 | **PASS** |
| 4 | Two reworks escape to the human instead of a third cycle | P4 | **PASS** |

## P1 — the whole chain, hands-off (spec ACHE-167, ticket ACHE-168, 18:30 → 18:36)
One AC (`kv has <key>`) on `kv-cli`, hand-built spec and ticket, then one promotion and no
further human action. The reviewer created its own three stages, and every stage ran once.

Verified independently afterwards, not taken from the reports:

| Commit | Role | Files | Test-file deletions |
|---|---|---|---|
| `60926cc` | red | `main_test.go` 48+/0- | — |
| `8fa5ec7` | green | `main.go` 7+/2- | **0** |
| `09ef1d5` | docs | `README.md` 3+/1- | 0 |

At `60926cc` the suite fails on **behaviour assertions** (`want stderr ... not found`,
`usage does not list "has <key>"`), not on a compile error — the "fail for the right reason"
rule holds in practice. At `09ef1d5`: 16 tests pass, `gofmt` and `go vet` clean. The three
`Head SHA`/`Red SHA` values chain red → green → docs, the ticket's `Head SHA` is the docs
head, and PR #6 opens on that same head, so the head a human merges is the head that was
verified. `Gate = PR review`.

Cost: **8 runs, 1 of them the leader, 0 comment wakes, 38,673 non-cache tokens.** For
comparison T3/v7-a1 spent 7 leader runs of 30 on three tickets.

## P2 — a Red SHA that is green (spec ACHE-172, 18:39 → 18:44)
Injected fault: a commit (`0f4728d`) carrying `TestCountPrintsNumberOfKeys`, named for AC1
but asserting only `kv list`, so the suite is **green** there. `Red SHA` was set to it and a
report was planted claiming it covered AC1.

The reviewer checked out `0f4728d`, ran the suite, got `13 passed, exit=0`, and rejected:
`Result = REWORK`, a `**Brief (cycle 1)**` naming each AC1 assertion that was missing, and a
two-write restart. The timeline is the proof:

```
18:39:40  backlog -> done      member   (the injection)
18:40:31  done -> backlog      agent    (write 1)
18:40:31  backlog -> todo      agent    (write 2)
18:41:05  todo -> in_progress  agent    (sq-qa actually ran)
18:41:41  in_progress -> done  agent
```

`sq-qa` then wrote five real tests that fail on assertions at `e8381e5`, and the ticket
completed PASS. Two further findings:

- The reviewer understood that stage 2's no-deleted-test-lines check must diff against the
  **new** `Red SHA`, so legitimately replacing the planted test did not trip it. It said so
  before stage 2 ran.
- `sq-qa` read the injection commit message, recognised the planted fault, and said in a
  comment that replacing the test would hide what it was planted to catch — then did the work
  in the same run.

## P4 — the escape (spec ACHE-177, ticket ACHE-178, 18:47 → 18:49)
Same fault shape plus two `done → backlog` transitions planted on stage 1 while the ticket
was still `backlog`, so nothing was woken while they were created. Then one barrier.

The reviewer rejected the stage again and **stopped**, quoting its own rule: "Rework count is
already 2 … The ACHE-179 timeline shows two `done → backlog` transitions. The ticket
ACHE-178 and stages ACHE-180 and ACHE-181 have none. That makes 2, the limit." It set
`Result = REWORK` on the ticket and closed it; the leader set `Gate = Decision needed` and
the spec `in_review`, with a Status comment naming the decision and offering Retry or Stop.
Stage 1 was never reopened a third time and stages 2 and 3 were never promoted, so no
implementation and no PR exist on that branch.

This is the whole replacement for v7's `@mention`-then-`blocked` escalation, and it is the
only one of the four claims that had no measurement behind it before today.

## Platform facts the probes added
- **A human's comment wakes an agent-assigned issue's assignee** (`kind: comment`, measured
  on `ACHE-174` at 18:39:56). Only an *agent's* comment on an agent-assigned issue wakes
  nobody. A planted report therefore costs one extra run, which is why P2 shows two `sq-qa`
  runs where a real cycle has one.
- **A restart is queued, not dropped, when a run is already in flight on the same
  (issue, agent)**: the 18:40:31 restart started at 18:40:44, the instant the earlier run
  ended. `HasPendingTaskForIssueAndAgent` deduplicates a *pending* task, it does not discard
  a promotion.
- **`→ done` and `done → backlog` start no run, and a `backlog` parent gets no barrier
  notification** — which is what makes a probe like P4 constructible at all: five issues, two
  planted reopens, zero runs until the one barrier was fired deliberately.

## Open finding, not blocking
Commits are authored as `sq-implementer@multica.local` / `sq-doc@multica.local`, not
`squadbot` — found by the reviewer itself, under `Risks`, on both P1 and P2. The
`handoff-protocol` skill says to *push* as `squadbot` and says nothing about commit
authorship, so each agent used its own identity. Arguably better attribution; it is recorded
here because the PR's commits now carry an identity no instruction asked for.

## Next
The ADR 0002 gate is met, so the config is frozen and T3 runs three times for pass^3.
