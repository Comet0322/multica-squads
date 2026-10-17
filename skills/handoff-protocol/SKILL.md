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
