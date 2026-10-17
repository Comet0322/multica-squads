---
name: handoff-protocol
description: Standard format for delegating work and reporting results between squad members
---

# Handoff protocol

## Delegating (leader -> member)
Post an issue comment mentioning the member with:
- **Goal**: one sentence.
- **Inputs**: files, branches, prior comments to read.
- **Output**: exactly what to deliver.
- **Verify by**: the command or check that proves it is done.

## Reporting (member -> leader)
Post a comment mentioning the leader with:
- **Done**: what changed (files, branch/commit).
- **Verified**: commands run and results.
- **Risks / open questions**.
- **Verdict** (reviewers and QA): APPROVE/CHANGES REQUESTED or PASS/FAIL.

Keep one task per handoff. Do not do work outside your role.

## Status rules (autonomous by default)
Humans are not part of the loop unless the spec says so. Never leave a task waiting for a person to press a button.

- **Finished your task** (whatever the verdict): post the report, then set your own sub-issue to `done` yourself: `multica issue status <id> done`. A failed review or QA is still a finished task; the verdict goes in the comment and the leader creates rework. Finishing is what wakes the leader to start the next stage.
- **`blocked`**: only when you hit a problem you genuinely cannot resolve yourself (missing access, contradictory requirements, an external dependency). Say exactly what is needed and from whom. Try to solve it first; ambiguity you can resolve by reading the spec or code is not a block.
- **`in_review`**: only when the spec or issue explicitly says a human must approve before work continues. Never use it as a "finished" state.
- Do not ask the user for confirmation of routine decisions.
