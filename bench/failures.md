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

## 2026-10-17 — four defects on the only paths the fast path and the PR relay can take
**Class:** spec-wrong (instructions), found by tracing rather than running.

B2 and B3 were traced through `agents/medic.md`, `agents/lead.md` and the measured platform
facts instead of being executed, because each live mechanism check costs ~30 min and ~300k
tokens. The trace found four defects, each on a path that is not optional but the *only*
path the mechanism can take:
1. medic's Job 2 posted its relay comment and then `rerun`-ed the spec — the identical
   double wake F17-2 found in Job 1, in the identical shape, with the identical risk of two
   leaders opening one rework twice.
2. PR feedback was to become a handoff under a ticket already set `done`, relying on a stage
   barrier firing on a `done` parent, which nothing has ever verified.
3. The spec stayed `in_review` while that rework ran, and medic's Job 1 only scans
   `in_progress` specs, so the one window where a human is explicitly involved was the one
   window medic could not recover.
4. Phase 2b had no branch for a handoff child of the spec, which is the *only* structure the
   fast path produces, so every fast-path wake would have been improvised.

**Lesson:** a fix applied to one job does not propagate to the other job of the same agent,
and a feature with its own structure (the fast path) needs its own branch in every phase
that structure can wake. Both are findable by reading the instruction for each path the
design admits — cheaper than a run, and it found what three live probes had not.

## 2026-10-17 — a single leader run created the same rework twice (B1, F1)
**Class:** agent-behaviour. Cost: one stray commit plus one extra rework round.

`ACHE-125` was created at 12:39:24 and `ACHE-127` at 12:39:49 with near-identical titles.
Both timestamps fall inside ONE leader run on `ACHE-116` (12:38:44 -> 12:40:04), so this was
not two concurrent runs reading the same state — it was one run repeating its own create 25 s
apart. The leader then cancelled `ACHE-127` itself, but not before it had been acted on: the
re-review (`ACHE-126`) reported that its only remaining blocker was the stray `.gitignore`
commit `ce4c28c` "left by the cancelled duplicate ACHE-127", which `ACHE-128` then reverted.

**What this corrects.** The concurrency hazard found by F17-2 (two leader runs 30 s apart
after medic's double wake) is real but was NOT the cause here, and it must not be used to
explain this failure. Measured separately: B1 had **12 overlapping leader-run pairs** and all
twelve were harmless, because every overlap was between a run on the spec and a run on a
different ticket — the normal pipelined handoff (a ticket finishes, the spec wake promotes
the next ticket, that ticket's run starts while the spec run is still finishing). Two runs on
the *same* issue never overlapped; consecutive ones were adjacent.

**Lesson:** at-least-once delivery is not the only source of duplicates — an agent can
duplicate its own call inside one run. The defence is the same either way and belongs in the
instruction, not in a lock: list what exists and compare by purpose before creating anything.
`sq-lead` also runs with `max_concurrent_tasks: 3`, so the instruction has to hold under both.

## 2026-10-17 — the scorer walked one level of a three-level family
**Class:** tooling. Found by re-auditing conclusions, not by a run.

`family = [parent] + [direct children]` predates v6's three levels. On B1 it saw **36 of 74
runs**, so `tokens` undercounted by 60% (128,879 vs 318,052), and `rework_issues`,
`review_changes_requested` and `qa_fail` scanned ticket issues only — but reworks are
handoffs and every reviewer/QA verdict is posted on a handoff, so all three were
structurally pinned at 0 for any v6 run. A human comment on a handoff issue was invisible
to the intervention count as well. The family is now walked transitively (paging
`issue list`, which caps at 100). Re-scored, B1 reports 29 sub-issues, 318,052 tokens and
34 leader wakeups, matching an independent count.

This was the SECOND defect in the same file. The first (the intervention metric) was found
by checking the metric against measured attribution data; this one was invisible to that
check because it is not about what a field means but about which issues are looked at.

**Lesson:** validating a metric against one run does not validate the set it was computed
over. Check the denominator too — "zero rework issues" from a scorer and "zero rework
issues" in the issue tree are different claims.

## 2026-10-17 — a stale results.csv header read as plausible data
**Class:** tooling. Caught while reading the re-scored row, before it reached a conclusion.

`score.py` wrote the header only when creating the file, so adding a column left every
later value shifted one place against its column name. The shifted B1 row read as
`rework_issues=7, qa_fail=3` when the truth was `ticket_count=7, rework_issues=4,
qa_fail=0` — wrong in a way that looks like a finding rather than an error, and it briefly
produced one. `score.py` now compares the file's header with its own columns and refuses to
append on a mismatch.

## 2026-10-17 — v7 design audit: four defects that would have stopped a run
**Class:** design. Found by reading the config against `docs/design-review.md` and the
platform source, not by running it. All four are v7-specific: they are consequences of
moving ownership down a level and of deleting the medic.

1. **Every escalation path was a dead end.** `reviewer.md` claimed setting a ticket
   `blocked` "fires the spec's barrier"; it does not — `isTerminalChildStatus` is `done` or
   `cancelled` only (`handler/issue_child_done.go:99`). The leader's `blocked` branch was
   therefore unreachable, and with no medic a `blocked` issue is a permanent stall. Fixed:
   escalation is an @mention comment on your own issue **first** (measured wake), then
   `blocked`.
2. **One finished handoff woke its owner twice.** The protocol required a report to
   @mention its owner, and setting the issue `done` fires the barrier about a second later;
   deduplication is per (issue, agent) (`HasPendingTaskForIssueAndAgent`), and these are two
   different issues. Measured in B1: `ACHE-122`'s report woke `sq-lead` at 12:36:25 and the
   barrier woke it on `ACHE-116` at 12:36:26 — **17 of B1's 74 runs** were woken by a comment
   rather than by a barrier or a promotion. Harmless in v6, where the second run only chatted; in v7 the owner's wake
   promotes stages and reopens issues, so two runs on one state can do it twice. Fixed:
   reports @mention nobody, and `score.py` now counts `double_wakes`.
3. **Deciding which stage finished from `total`/`done` counts breaks after a reopen.** After
   a QA FAIL the qa handoff stays `done` carrying a stale `FAIL`, so once the reopened
   implement stage completes, both stages read complete, the owner concludes "qa finished",
   re-reads FAIL and reopens implement again — forever, with the two-cycle escape landing in
   defect 1. Fixed two ways: the owner reads the barrier's own system comment, which names
   the closed stage, the finished sub-issue and the next stage
   (`handler/issue_child_done.go:366`), and reopening a stage now resets the higher stages to
   `backlog --no-start`.
4. **The fast path had no implementation below the leader.** `reviewer.md` knew two ticket
   shapes, so a fast-path ticket would have been given a qa stage the user explicitly
   declined, no stage would have opened the PR, and "no ticket `done` without QA's PASS" made
   it unclosable; `lead.md` had no branch for "the only ticket finished", so the spec would
   never have reached its human gate. The same class of hole B3's trace found in the leader,
   reproduced in the new owner. Fixed: a `Mode: fast-path` ticket shape, its own closing
   rule, and a last-ticket branch in the leader.

Also fixed: a stall below the ticket level was invisible to everyone (the leader now checks
`runs --siblings` across the family and reruns the *ticket*, which re-enqueues its owner);
`qa.md` and `doc.md` never learned the reopen/cycle rules that `implementer.md` got;
the reviewer's integrity check sat above the dispatch that says which kind of issue woke it;
one `Verdict` vocabulary served two roles with nothing checking who wrote which value
(`score.py` now reports `verdict_role_mismatch`); and a fix ticket after the PR was open left
the merged head with no whole-spec check (the leader now reopens `Deliver` once the fix
ticket is `done` — never in parallel, because a stage completing while a lower stage is open
fires no barrier at all).

**Lesson:** the two defects that mattered most came from the same source — an instruction
that *asserted* a platform behaviour ("that fires the barrier", "the highest done stage is
the one that finished") instead of citing a measured one. Every such assertion in the config
is now either sourced or deleted.

## 2026-10-18 — T3 / v7 attempt 1: nothing failed, two things worth writing down

The first v7 run (spec `ACHE-152`, config `cbb276a`) succeeded hands-off: hidden 6/6,
existing green, build/vet/gofmt clean, `main` untouched, 0 interventions, 0 rework,
26.6 min. No entry here is a failure. These two are recorded because a clean run is the
only place to see them.

**1. An unavoidable duplicate wake, absorbed (cost, not defect).** The `child_done` barrier
is one `mode: continuous` rule on `issue.status_changed` with condition
`{children_done, each_stage: true}`. It keeps no record of having fired, so it re-evaluates
on **any** child status change and wakes the owner again whenever some stage is fully
terminal. The owner's own promotion of the next stage is such a change, so every stage
transition costs one extra owner wake for the stage that just closed. Measured: stage 1
closed at 16:31:17, and at 16:32:24 — the instant F1 went `backlog → todo` — the same rule
fired again with `stage: 1, total: 1, outcome: woke`. The second leader run returned
`no_action — "Stage-1 barrier re-fired; F1 (ACHE-154) already promoted and running, nothing
to advance"`. This is the first time the rule "every owner wake re-checks its own level and
leaves anything moving alone" has been observed earning its keep against a real duplicate;
an owner whose first act were to advance a stage would have promoted twice. Written into
`CLAUDE.md` and as row 10 of the wake inventory in `docs/design-review.md`, where no row had
covered it.

**2. Two reporting defects of my own, one in the config and one in the scorer.**
- `lead.md` §146 calls the `**Status**` comment "the human's only progress view" and says to
  keep one and update it. The leader did exactly that — and also posted 5 narrative progress
  comments on the spec, so the human has 6 things to read where the design promises 1. The
  instruction forbids no other comment, which is the hole: §152 and §161 legitimately need
  `**Spec correction**` and answers-to-humans, so the fix is a positive rule ("progress goes
  in the Status comment and nowhere else"), not a blanket ban. Not fixed yet; it changes
  synced config, so it waits for the user's call on the remaining runs.
  Upside confirmed by the same 5 comments: a leader's own comment on the squad-assigned spec
  wakes nobody (5 comments, 0 comment-kind runs), so `handler/squad.go:1155` self-suppression
  holds in practice.
- `score.py`'s `double_wakes` reported 1. It is the spec's **first** leader run, whose
  `attribution.evidence.kind` is `comment` pointing at the Status comment created 1 s
  earlier, while the run was actually started by the spec's own `backlog → in_progress`
  promotion 23 s before that. So the metric mis-classifies the opening wake of every family.
  It is a candidate condition, not part of `success`, so the result stands; the fix is to
  ignore a comment-kind wake whose issue left `backlog` within the same minute. Unfixed,
  together with `rework_reopens` (F3), which still matches `done → todo` and is therefore
  structurally 0 for every v7 run — both live in the bench tooling the user asked me to stop
  touching, so both need the user's call.

## 2026-10-18 — agent commits authored as the human (measurement integrity)

Found by `sq-reviewer` itself, under `Risks`, on both v8 probe PRs: the commits were authored
`sq-implementer@multica.local` and `sq-doc@multica.local`, which no instruction had asked for.
Checking the history turned up something worse. On `fix/kv-bugs-v7-a1` — the branch of the
**scored** T3/v7-a1 run — commit `8bf98b7`, which is the `Head SHA` recorded on handoff
`ACHE-158` and therefore `sq-implementer`'s work, is authored `Comet0322
<jerrymark611@gmail.com>`. The same `sq-doc` appears as `@noreply.invalid` on one branch and
`@multica.local` on another.

**Cause (verified).** `multica repo checkout` hands the agent a **git worktree**, and a
worktree shares the repository's `.git/config`. Both `kv-bugs` and `kv-cli` have
`user.email=jerrymark611@gmail.com` configured locally, so an agent committing there inherits
it; where the config supplied no name, the runtime filled in `<agent>@multica.local`. The
agent never chose an identity and had no way to avoid one.

**Why it matters.** `human_interventions` is computed from issue timelines, where this leaves
no trace at all, so the scorer still reports 0 and the run is still genuinely hands-off. But
anyone auditing the branch instead of the tracker sees a person's name on an agent's commit —
and the claim the whole benchmark exists to support is precisely that the squad did the work
unaided. Evidence that contradicts itself is worth less than evidence that is merely thin.

**Fix.** `handoff-protocol` now pins the identity on the command itself:
`git -c user.name=squadbot -c user.email=squadbot@localhost`, with a `Co-Authored-By` trailer
naming the agent, so the author matches the pusher and the per-stage attribution survives.
`-c` and never `git config`, because a `git config` write inside a worktree lands in the
config the whole repository shares — the very thing that caused this.

**Not retrofitted.** T3/v7-a1's branch is left exactly as it is: rewriting a scored run's
history to make it look better is not available. The row stands with this entry attached.
