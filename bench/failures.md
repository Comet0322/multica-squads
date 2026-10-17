# Failure-mode ledger

Every observed failure of a scored run or a deterministic probe, classified, with
the evidence and the design change it caused. Append-only; never rewrite an entry.
A version claims an improvement by showing its targeted mode no longer occurs plus
a passing probe for it — not by a higher pass count (see `rubric.json`).

Modes: `platform` · `spec-wrong` · `integration-miss` · `review-miss` · `tooling` · `cost` · `other`

---

## 2026-10-17 — T3 / v4 attempt 1 (ACHE-75) — `platform`
**What happened.** The platform paused the `child_done` wakeup rule after it had
started 12 runs within an hour (`wakeup_paused`, `reason: rate`, `limit: 12`, at
07:27Z). It does not auto-resume. A person had to wake the leader by hand.

**Evidence.** `multica issue timeline ACHE-75` → `wakeup_paused` at 07:27:26Z;
run at 07:43:46Z with `attribution.source = direct_human`, trigger summary
"Platform paused the automatic child_done…". Upstream cause read in
`server/internal/service/issue_wakeup.go:1292-1316` (`wakeupHourlyRunLimit = 12`).

**Caused.** v5's issue restructure (per-ticket handoffs keep each issue far below
12 triggers) and v6's `sq-medic` recovery agent + the three fault-injection probes.

---

## 2026-10-17 — T3 / v4 attempt 1 (ACHE-75) — `platform`
**What happened.** After the PR stage finished, the leader was never woken again,
so the spec issue was left mid-flow. A person had to start it by hand a second time.

**Evidence.** Run at 08:04:35Z with `attribution.source = direct_human`, trigger
summary "All stages are done including docs (ACHE…". This wake left **no** member
timeline entry, so the original scorer could not see it.

**Caused.** v6 scorer counts `direct_human` runs as interventions (deduped against
member comments), and `sq-medic` Job 1 detects "stage complete, nothing running".

---

## 2026-10-17 — measurement defect found while scoring v6 (`tooling`)
**What happened.** Re-scoring ACHE-75 with the v6 scorer gives
`human_interventions = 3`, not the 2 recorded in `results.csv`. The old count was
right by coincidence: it counted one human comment plus the final manual status
change, and missed the second hand-started wake entirely.

**Evidence.** `bench/runs/ACHE-75.json`: 37 runs, `direct_human` 2, `delegation` 35.
Peak leader context on that run: 1,229,462 cache-read tokens in a single run.

**Caused.** The recorded T3/v4 row keeps its original number (records are never
rewritten); v6 rows use the corrected definition. Noted here so the two are not
compared as if they measured the same thing.

---

## 2026-10-17 — C-layer probe C1 was mis-designed (`tooling`)
**What happened.** C1 was meant to test the boundary clause "a bug nobody can
reproduce". Its message said *"We have no reproduction and no logs"*, which is a
different claim: it says the reporter has none, not that none can be obtained. The
leader checked out kv-cli, found a real lost-update race, reproduced it, proposed a
locking fix and asked four questions. It created nothing. So the probe failed while
the squad behaved exactly as v6 asks.

**Evidence.** Leader reply: "50 parallel `kv set` calls … keys written: 50, keys
present: 32", "I ran 20 trials of 20 parallel `kv set` calls, and all 20 lost keys",
then four questions and "Nothing has been created yet: no issues, labels or branches."
Issue max identifier and label count unchanged (ACHE-104, 16).

**Caused.** C1 is retired (`pass = void` in `probes.csv`, never counted as a squad
failure) and replaced by C1b, whose report genuinely cannot be reproduced: one
sighting three weeks ago, key unknown, store overwritten since, no logs. C1b passes
and cites the Reproduction clause by name. General lesson for probe design: a
refusal probe must remove the *capability*, not merely the reporter's information —
otherwise the leader can satisfy the boundary by doing the missing work itself.

**Side finding (not a failure).** Two independent probes (C1, C3) found the same
unsynchronised read-modify-write in **kv-cli**, which is the same defect T3 reports
as a symptom in kv-bugs. T3's hidden bug is therefore easy to find from the code,
and T3 measures the delivery flow rather than diagnostic difficulty.

---

## 2026-10-17 — the scorer's intervention metric was wrong for v6 families (`tooling`)
**What happened.** `attribution.source` does not mean what the v6 scorer assumed.
It names the human or agent at the **root of the causal chain**, not who started the
run. So `source == "direct_human"` was both a false positive and incomplete, and the
fault-injection probes exposed it before any scored run was spent.

**Evidence.** Measured, not reasoned:

| what really started the run | `source` | `evidence.kind` | `wakeup_system_rule` | `delegated_from_task_id` |
|---|---|---|---|---|
| a person comments, the agent wakes | `direct_human` | `comment` | – | – |
| a person fires a rule by hand (`wakeup trigger`) | **`trigger_owner`** | `issue_wakeup` | – | – |
| the platform's stage barrier, agent-built family (ACHE-75) | `delegation` | `issue_wakeup` | `child_done` | yes |
| the platform's stage barrier, hand-built family (ACHE-105/109) | **`direct_human`** | `issue_wakeup` | `child_done` | – |
| `sq-medic` restarting with `issue rerun` (ACHE-110) | `direct_human` | `issue_assignment` | – | – |
| an agent's comment or assignment | `delegation` | `comment`/`issue_assignment` | – | yes |

Two defects follow. **False positive:** every stage-barrier wake in a family a person
built is `direct_human`; scoring the F17-3 probe family with the old code gives 4
human interventions for a run that recovered by itself. v5 moved the squad from
agent-created wakeup rules to platform stage barriers, so this would have hit every
v6 scored run. **Incomplete:** a person hand-firing a wakeup rule is `trigger_owner`,
a source the old code never looked at, so that intervention counted as zero.

**Caused.** `bench/score.py` no longer reads `source` at all. It asks what *explains*
a run — a platform rule (`wakeup_system_rule`), another agent's task
(`delegated_from_task_id`), or an `sq-medic` restart (one per `**Medic**` comment,
within 300 s) — and counts anything unexplained as a person. Re-scoring ACHE-75 still
gives 3, so the v4 number is unchanged; the F17-3 family now gives 2 human
interventions (the two status changes used to build it, which really were mine) and 1
auto-recovery.

**Also settled.** An agent running the `multica` CLI *is* recorded as `actor_type:
agent` in the timeline — sq-medic's `**Medic**` comment and sq-doc's handoff comment
both are. That was the v6 scorer's last unverified assumption, and it is why a
recovery costs no bot account.

---

## 2026-10-17 — the v6 capability boundary refused greenfield work (`spec-wrong`)
**What happened.** B1 could not start. Asked for a new CLI in the empty `csvstat`
repo, the leader refused: Phase 0 required "a repository that already has a test suite
you can run", and an empty repo has none. The refusal was well argued and listed
exactly what the repo would need.

**Evidence.** Leader reply: "the repo needs a test suite we can already run. I checked
out `csvstat`. It has one commit … There's no `go.mod`, no Go code and no tests, so
`go test ./...` has nothing to run." Nothing was created.

**Why this was the instructions' fault, not the squad's.** `agents/lead.md` said both
things at once: Phase 0 demanded an existing test suite, while Phase 1 said "a new
project may have an empty repo; that is fine". The agreed v6 scope puts greenfield in
tier B — a mechanism that must work — and all four experiments already run were
greenfield, so the boundary as written would have refused every one of them. The
leader picked the safer of two contradictory readings, which is the right instinct.

**Caused.** 131e892 makes the distinction explicit: an **empty** repository is inside
the boundary, because the squad writes all the code and there is no untested work to
regress, and the first ticket must establish the build and the test command; a
repository that **has code but no tests** stays outside it, because review and QA
would have no baseline to protect. C9's probe note now says which of the two its
wording means. Re-run of B1 after the fix: the leader accepted and quoted the new
rule back ("An empty repo is fine: the first ticket sets up `go.mod` and
`go test ./...`").

**Lesson for the design.** A boundary condition is only safe if it is stated as the
*reason* it exists. "Already has a test suite" was a proxy for "there is a baseline to
protect"; written as the proxy, it excluded a case the reason does not.
