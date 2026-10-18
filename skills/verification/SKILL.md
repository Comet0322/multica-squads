---
name: verification
description: Gatekeeping: rerun the checks yourself and decide PASS, FAIL or BLOCKED for each acceptance criterion against objective evidence
---

# Verification (gatekeeping)

One question: for every acceptance criterion, is there objective evidence that it is satisfied? Run commands, read output, map item by item — not "I feel it's fine".

The gate issuer is a different party from the gated. An author can self-check and paste the output, but only a non-author's rerun is a gate.

1. Read the acceptance criteria on the issue.
2. Map every criterion to evidence: which test, which command, which output.
3. **Rerun** the commands on the pushed head. Never cite someone else's described output.
4. Check scope: does the diff touch only this requirement?
5. Give PASS or FAIL per criterion.

Result:
- **PASS** — every criterion has sufficient evidence.
- **FAIL** — at least one is unmet. Give the problem, why it matters, where, and the fix direction. Never edit the artifact yourself to fix it.
- **BLOCKED** — information or environment missing, cannot verify. Say so; never turn it into PASS.
