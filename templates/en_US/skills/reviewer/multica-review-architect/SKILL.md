---
name: multica-review-architect
description: "Architecture-design dedicated review framework. Called by ArchReviewer to analyze the technical architecture design produced by Architect across multiple dimensions, output PASS/FAIL with an ID-numbered fix list, and report to Leader."
---

# Architecture Design Professional Review (ArchReviewer)

This skill provides a structured professional review framework for **technical architecture design artifacts**. It is called by `ArchReviewer`; the review target is the design link that `Architect` returns via `multica-artifact-architect`.

## When to use

- ArchReviewer receives a "review architecture design" task dispatched by Leader.
- Entering a re-review round after design changes (check the previous round's fix list + the **review response** table item by item).

## Pre-review check (metadata)

The design document must have a metadata table under the H1; a missing item, or a re-review draft whose version was not bumped, can be an immediate FAIL:

| Check | FAIL condition |
| --- | --- |
| Creator / created time / version / status / JIRA / upstream PRD | Any of them missing |
| Re-review draft version | Not higher than the previous round (e.g. still v0.1 yet claims to be revised) |
| Revision history | Inconsistent with the version, or missing an entry for this round |
| Review response | Re-review draft does not respond item by item to the previous round's blocking items |

## Review dimensions (conclusion per item)

Mark each item **PASS / FAIL / N/A**. A FAIL must go into the fix list with a **REV-n** ID.

### A. Document and process

1. **Metadata and version**: header information complete; revision history consistent with the version.
2. **Review response completeness** (re-review): whether the previous round's REV-n items are answered one by one; whether rejected items have sufficient reasons (they may still block; Leader arbitrates).

### B. Solution quality

3. **Soundness**: layering, module boundaries, dependency direction clear; no over-design or obvious under-design.
4. **Scope and non-goals**: consistent with PRD/Issue; non-goals explicit; no implicit scope expansion.
5. **Alternatives and trade-offs**: whether it explains why a simpler solution was not used (always ask when complexity is high).

### C. Correctness and consistency

6. **Acceptance alignment**: line-by-line coverage of AC-/FR-/BR-; the **requirements traceability** table is complete with no dangling AC.
7. **Cross-end consistency**: frontend/backend/UI contract boundaries are self-consistent; state machines and error semantics do not conflict.
8. **Data and consistency**: entity/field changes are clear; read/write ownership, transaction boundaries, and the historical-data strategy are explicit.

### D. Reliability and security

9. **Failure modes and degradation**: behavior on dependency failure, timeout, or partial failure; whether it is acceptable.
10. **Concurrency and idempotency**: whether duplicate requests, races, and retry strategy are defined.
11. **Security and permissions**: authentication/authorization, sensitive data, auditing; whether the team baseline is met.
12. **Key technical risk**: performance, capacity, and consistency risks identified with mitigations; **no mitigation = blocking**.

### E. Deliverable and operable

13. **Extensibility and maintainability**: cost of common changes; whether hard-to-reverse tech debt is introduced.
14. **Testability**: whether the verification plan is executable; whether implementation steps map to tests.
15. **Migration and rollback**: data migration, release order, feature flags, rollback path (mandatory when applicable).
16. **Observability**: whether logs, metrics, and alerts are sufficient to diagnose production issues.

### F. Open items

17. **Pending decisions**: whether DECISION-/BLOCKED items block entering development; whether Leader/PM must close them.

## Output format

```text
[Architecture Design Review] <design link>
Document version: v0.x (metadata table)
Conclusion: PASS / FAIL

Metadata check: PASS / FAIL - <note>

Dimension summary:
- A Document and process: ...
- B Solution quality: ...
- C Correctness and consistency: ...
- D Reliability and security: ...
- E Deliverable and operable: ...
- F Open items: ...

Blocking items (required on FAIL; stable IDs make re-review checking easy):
- REV-1 | dimension | rationale | section/AC involved | fix direction
- REV-2 | ...

Suggestions (non-blocking):
- SUG-1 | ...

Check against previous round (on re-review):
- REV-x: resolved / unresolved / rejected, pending Leader arbitration
- Resolved X / unresolved Y

Round: N / 3
```

The conclusion and fix list are **reported to Leader**; do not modify the design or notify Architect yourself.

## Review principles

```text
Risk without mitigation        -> blocking
Dangling AC-                   -> blocking
Re-review without version bump -> blocking
Scope creep without basis      -> blocking
"Will add later"               -> blocking (unless written into pending decisions and Leader agrees to a conditional PASS)
```

## Boundaries

- Review only architecture design, not UI visuals, product priority, code implementation, or test-case details.
- Does not replace Leader's generic gate (`multica-verification` skill).
- Still FAIL at round 3 -> mark "escalate to human", hand to Leader, stop looping.

## Why this works

A list with REV-n IDs + document version + review-response table makes multi-round revisions traceable; the 17 dimensions cover angles Architects easily miss (data, security, operations), reducing design defects discovered only after G2.
