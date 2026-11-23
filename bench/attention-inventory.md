# Attention inventory — what a requester sees of a `dev-team` run (config v8, T3)

Baseline for the `attention_cost` metrics in `rubric.json` (v4). Measured 2026-11-23 from the
original benchmark database (`multica_ui` inside the `multica_pgdata` volume, workspace
`achernar`): specs ACHE-182, ACHE-196, ACHE-210, the three scored v8 runs. v9 and the flat
`dev-flat` idea have not been run; this is the number they have to beat.

"Visible" = no `internal` label, which is the board's default filter.

## Issues per run (identical in all three)

| level | what | issues | visible | internal |
|---|---|---|---|---|
| 0 | the spec | 1 | 1 | 0 |
| 1 | spec-check + 3 tickets | 4 | 3 | 1 |
| 2 | handoffs: 3 stages x 3 tickets | 9 | 0 | 9 |
| | **total** | **14** | **4** | **10** |

71% of the issues in a run are internal. If the filter is off, or the requester wants to see why a
run is slow, they face 14 issues and ~28–30 agent runs for a 3-bug fix.

## Comments per run (all by agents; no person wrote one)

| level | a1 (ACHE-182) | a2 (ACHE-196) | a3 (ACHE-210) |
|---|---|---|---|
| 0, the spec | 5 | 5 | 6 |
| 1, spec-check + tickets | 13 | 14 | 15 |
| 2, handoffs | 10 | 9 | 11 |
| **total** | 28 | 28 | 32 |

Roughly 18–21 comments sit on visible issues (spec + tickets) and 9–11 on internal ones.

## What is on the spec in a1 (the one issue the requester is promised to read)

| # | comment | by design? |
|---|---|---|
| 1 | `**Status**` | yes, the single kept-updated status |
| 2 | `**Spec correction** (1)` | yes, a rejected-spec recovery |
| 3 | "Ticket 1 is done and passed, so I started ticket ..." | **no, narration** |
| 4 | `**Spec correction** (2)` | yes |
| 5 | "All three tickets passed and the pull request is open: ..." | no, but it is the one comment that tells the requester the result |

So 2 of 5 are narration, and one of those carries the PR link. `lead.md` promises one comment; the requester
reads five. Not a large number, but the design says one and nothing enforces it.

## What this says

- **The 14-issue shape is structural, not noise.** Three stages per ticket is the design (ADR 0002), so the
  hidden-issue count scales as 3 per ticket + 1 spec-check; a 6-ticket spec is 22 internal issues.
- **The `internal` label is the only thing between the requester and that.** It is applied by the leader's
  instructions, not by the platform, and nothing checked in v8 that it is on every handoff. The scored runs
  show 30 `internal` labels over three runs (10 per run), matching 1 spec-check + 9 stages, so it held here.
- **A stall is invisible.** `watch.py` is an operator tool; a stalled run reads as `in_progress`. ADR 0001
  accepts this, but the requester has no way to tell "slow" from "stuck".

## Reproduce

```sql
-- psql against the benchmark DB; family = spec + all descendants
with recursive fam as (
  select id, number, 0 lvl, number as spec from issue where number in (182,196,210)
  union all select c.id, c.number, f.lvl+1, f.spec from issue c join fam f on c.parent_issue_id=f.id)
select f.spec, f.lvl, count(*) issues,
  count(*) filter (where coalesce((select string_agg(l.name,',') from issue_to_label il
        join issue_label l on l.id=il.label_id where il.issue_id=f.id),'') not like '%internal%') visible
from fam f group by 1,2 order by 1,2;
```
The database is not part of the running server: it lives in the old `multica_pgdata` volume and was read from a copy.
