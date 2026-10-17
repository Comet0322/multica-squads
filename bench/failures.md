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
