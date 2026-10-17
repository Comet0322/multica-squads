---
name: definition-of-done
description: Checklist a task must satisfy before it is considered complete
---

# Definition of done

- Every acceptance criterion is met and demonstrated.
- New behavior has tests; the full test suite passes.
- Linters and type checks pass.
- The ticket's owner approved the change with no unresolved blocking comments (`Review verdict: APPROVE` on the handoff it judged).
- QA verified the built result, not just unit tests (`QA verdict: PASS`), on the same head the owner is blessing. The one exception is a fast-path ticket, which the user explicitly approved without QA; there the owner's own APPROVE plus the open PR is the record.
- The issue comment history states what was delivered and how it was verified.
- Evidence is pasted command output, not a claim. "Tests pass" without the command and its real output is not evidence, and a reviewer or QA report that contains none is incomplete.
