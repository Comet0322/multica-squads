---
name: multica-technical-design
description: "Produce a minimal technical plan from the PRD and the existing code. Used by @Architect for architecture analysis, impact assessment, and implementation-plan design; includes document metadata and re-review revision rules; once the draft is ready, hand it to multica-artifact-architect to land it."
---

# Technical Design

## Purpose

Based on the PRD (or Issue) and the existing codebase, produce the **smallest viable** technical design (this skill owns "what to write", not "which platform it lands on").

> Division of work with `multica-artifact-architect`: **technical-design produces structure and content; artifact-architect validates the artifact and lands it through the Confluence/JIRA platform skills**.
> Works with `multica-review-architect`: **first draft -> review -> revision -> re-review** (at most 3 rounds); each revision must bump the version and fill in the "Review response".

## Platform collaboration

| Platform skill | Use in this skill |
| --- | --- |
| `multica-platform-jira` / `multica-platform-confluence` | Read the PRD / Issue (before starting); **writes** are orchestrated by `multica-artifact-architect` |

This skill only produces the local `design.md`; for credentials and the publishing CLI see the platform skills.

## Process

1. Read the PRD / Issue and the acceptance criteria (AC-/FR-/BR-).
2. Inspect the current implementation (prefer codegraph / existing patterns; do not sweep the repo broadly).
3. Identify the relevant modules and existing patterns.
4. Determine the smallest viable change; state the **non-goals** clearly.
5. Identify data / interface / non-functional impact and dependencies (RISK-, DECISION-).
6. Define the verification method (aligned with AC-); fill in the **requirements traceability** table.
7. Write the document **header metadata** (creator, created time, version, status).
8. Insufficient information -> BLOCKED, record it under "Pending decisions"; do not guess.

## Principles

```text
Existing patterns > new abstractions
Small changes     > big refactors
Reuse             > new dependencies
Verifiable        > unverifiable ideas
Rollbackable      > one-shot irreversible changes
```

## Local draft path

```text
docs/design/<ISSUE-KEY>/design.md
```

For the baseline sections see `multica-platform-confluence/scripts/templates/design-template.md`.

## Document header (mandatory, under the H1 title)

The **first block** of the design body must be the metadata table, so ArchReviewer can track version and owner:

| Field | Rule |
| --- | --- |
| **Creator** | `Architect-<member-id>` (matches the Squad member) |
| **Created time** | `YYYY-MM-DD HH:mm` (team-agreed timezone, default UTC+8) |
| **Version** | Semantic `v0.1` onward; **bump on every review-driven change** (v0.2, v0.3 ...) |
| **Status** | `Draft` -> `In review` -> `Approved`; use `Deprecated` for abandoned designs |
| **JIRA** | Issue Key |
| **Upstream PRD** | Link to the Confluence requirement page (resolve it from JIRA; never leave blank) |

Example:

```markdown
# Technical Design - PROJ-1813 Chunked Upload

| Field | Value |
| --- | --- |
| **Creator** | Architect-u1024 |
| **Created time** | 2026-08-26 15:30 |
| **Version** | v0.1 |
| **Status** | Draft |
| **JIRA** | PROJ-1813 |
| **Upstream PRD** | http://confluence.../pages/viewpage.action?pageId=... |
```

## Output (must include)

| Section | Required | Content |
| --- | --- | --- |
| **Document header** | Yes | Creator, created time, version, status, JIRA, upstream PRD |
| **Understanding** | Yes | What the system currently does; aligned with the PRD scope |
| **Non-goals** | Yes | What is explicitly not done, to prevent scope creep |
| **Proposed changes** | Yes | Smallest viable plan; optionally a short "alternatives and trade-offs" |
| **Affected components** | Yes | File / module / service - change type - notes |
| **Data and state** | When applicable | Entity/field/state changes; consistency requirements |
| **Interface and contract boundaries** | When applicable | Frontend/backend/UI boundaries; error and auth conventions |
| **Implementation steps** | Yes | Actionable steps for @FrontendDev / @BackendDev |
| **Non-functional requirements** | As needed | Performance, security, availability, observability measures |
| **Migration and rollback** | As needed | Data migration, feature flags, rollback steps |
| **Verification plan** | Yes | Verification item - method - corresponding AC- |
| **Requirements traceability** | Yes | AC-/FR-/BR- -> design decision -> implementation step |
| **Risks and boundaries** | Yes | RISK-n - risk - mitigation |
| **Pending decisions** | If any | DECISION-n; BLOCKED items |
| **Review response** | On re-review | Respond item by item to the ArchReviewer fix list |
| **Revision history** | Yes | Date - version - author - change summary |

## Architect writing angles (easy to miss)

Design reviews often probe these angles; cover them in the first draft where possible:

| Angle | Self-check question |
| --- | --- |
| **Scope** | Are non-goals clear? Is the requirement being quietly expanded? |
| **Data** | Who writes, who reads? Consistency / transaction boundaries? What about historical data? |
| **Concurrency and idempotency** | Are duplicate submissions, races, and retries considered? |
| **Failure and degradation** | What if a dependency is down? Is partial failure acceptable? |
| **Security** | Are authentication/authorization, sensitive data, and audit logs addressed? |
| **Performance** | Order-of-magnitude assumptions? Hot paths? Is async/caching needed? |
| **Testability** | Can implementation steps map to executable verification? |
| **Operations** | Deployment order, config items, monitoring/alerts, rollback? |
| **Cross-end consistency** | Does it conflict with the UI/API contract? Are error codes / state machines unified? |
| **Traceability** | Can every AC- be found a landing point in the design? |

## Re-review revision flow (with multica-review-architect)

1. Read the **ArchReviewer fix list** forwarded by Leader (including blocking-item IDs).
2. **Bump the version by 1** (e.g. v0.1 -> v0.2) and set the status to `In review`.
3. Fill the **Review response** table item by item: modified / not adopted (a reason is required).
4. Update the affected sections; append a row to the **Revision history**.
5. Self-check again -> `multica-artifact-architect` -> platform publish (a Confluence upsert with the same title updates the version).
6. Notify Leader that the design is revised, entering the next ArchReviewer re-review round (at most 3 rounds).

Not adopting a blocking item requires Leader arbitration; Architect must not close the review on its own.

## Handoff

```text
First use multica-technical-design to write docs/design/<ISSUE-KEY>/design.md (with header metadata),
then use multica-artifact-architect to self-check, publish per the platform skill, and return the link.
```

For the publish command see `multica-platform-confluence` (`publish_design.py --append-jira`).

## Why this works

Header metadata + version + review response make multi-round ArchReviewer reviews auditable and diffable; the sections covering data / non-functional / traceability angles reduce rework in the downstream implementation stage. "The smallest viable change" is also a verifiable principle: the smaller the change, the easier it is to verify (Leader rerun / Tester regression) and the lower the regression risk.
