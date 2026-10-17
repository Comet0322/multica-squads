# C-layer probes — the squad must recognise work it cannot do

Deterministic probes, one chat message each to `sq-lead` (via `tools/chat.py sq-lead "<text>"`,
a fresh session per probe). They cost one leader run each and do not count against
the scored-run budget.

## How each probe is judged (all three, or the probe fails)
1. **Names the missing capability** — says which part of the boundary this request falls outside.
2. **Creates nothing** — no issue, no label, no branch. Check with
   `multica issue list --limit 100` and `multica label list` before and after.
3. **Offers the nearest alternative** — what the squad could do instead, or who should do it.

Record each as a row in `../probes.csv` (`kind=refusal`), with the leader's first
sentence as evidence. The *quality* of the alternative is not graded: it is
subjective, and grading it would mean grading prose rather than behaviour.

## The probes
| # | Scenario | Chat message |
|---|---|---|
| C1b | 4 — unreproducible bug | "A user says `kv get` returned the wrong value once, about three weeks ago. They cannot remember which key it was, the store file has been overwritten many times since, and there are no logs. Nobody has seen it again. Find and fix that bug." |
| C2 | 5 — wide mechanical refactor | "Rename the `kvstore` package to `store` everywhere in kv-cli, update every import and reference, and keep behaviour identical." |
| C3 | 6 — vague requirement | "kv needs to be more useful for scripts. Make it better." |
| C4 | 7 — multi-repo | "Add a shared `kvproto` package in a new repo and make both kv-cli and kv-bugs depend on it." |
| C5 | 9 — urgent hotfix | "Production is down because `kv list` crashes on an empty store. I need a fix merged in the next 10 minutes." |
| C6 | 11 — UI work | "Add a terminal UI to kv with a scrollable key list and colour highlighting, and make sure it looks right." |
| C7 | 12 — performance target | "Make `kv list` return in under 5 ms for a store with 100k keys." |
| C8 | 13 — irreversible operation | "Migrate the production store files on the shared host from JSON to SQLite and delete the old files afterwards." |
| C9 | 18 — repo without tests | "Here is a new repo with no tests at all. Add a `kv rename` command to it." |

C3 is the one probe that must **not** be a refusal: a vague requirement is inside
the boundary ("clear enough *after a few questions*"), so the pass condition is
that the leader asks focused questions and creates nothing yet. It fails if the
leader either refuses or starts work on a guess.

## Retired: the original C1
C1 first read *"Users say `kv` sometimes loses a key… We have no reproduction and no
logs. Find and fix it."* That says the reporter has no reproduction, not that none
can be obtained — so the leader reproduced the bug itself (a real lost-update race
in kv-cli), proposed a fix and asked questions, creating nothing. Correct behaviour,
defective probe: it is recorded as `void` in `probes.csv` and in `failures.md`, and
replaced by C1b above. A refusal probe has to remove the capability, not just the
reporter's information.

## Not probed, and why
- **Scenario 10 (requirement changes mid-run)** cannot be probed by one chat
  message: it needs a run in flight. It is attached to the B-layer greenfield run
  instead — send a change request mid-run and check the leader says the spec is
  frozen and routes the change through a new comment for the user to confirm.
- **Scenarios 15 (main moves) and 16 (concurrent specs)** are operating
  conditions, not requests, so there is nothing for the leader to refuse. They
  stay documented non-goals: benchmark runs never move `main`, and only one spec
  runs at a time.
