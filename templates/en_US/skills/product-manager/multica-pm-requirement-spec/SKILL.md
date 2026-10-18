---
name: multica-pm-requirement-spec
description: "Product-manager requirement spec: structure an Issue / request into a numbered PRD (G-/FR-/BR-/AC-/KPI-/OP-/RISK-). Includes knowledge-base background lookup; once the structure is ready, hand it to multica-pm-artifact-publish for landing."
version: 2.0.0
metadata:
  orchestrates:
    - Team knowledge base (optional)
  origin:
    - multica-pm-requirement-spec
---

# PM Requirement Spec (product-manager requirement spec · content)

## Purpose

Turn an Issue, meeting conclusions and scattered ideas into **clear, reviewable, task-splittable** PRD content (this skill only covers "what to write", not "which platform it lands on").

> Division of labor with `multica-pm-artifact-publish`: **this skill = requirement spec and numbering; publish = landing and updating the PRD file (Git version: `docs/prd/<ISSUE-KEY>.md` in the product repo)**. To change where the PRD lands, change only publish, not this skill.

## Platform collaboration

| Platform skill | Use in this skill |
| --- | --- |
| Team knowledge base (optional) (`multica-platform-knowledge-base`) | Step 0.5: look up terms and historical requirement background (**reference only**, never treated as new AC) |
| `multica-platform-jira` / `multica-platform-confluence` | **Not called directly**; reading and writing is orchestrated by `multica-pm-artifact-publish` (in the Git version of this repo they are not used at all) |

For agent instructions see [`references/agent-instructions.md`](references/agent-instructions.md).

## Two phases (spec != submission)

| Phase | Action | Stop point |
| --- | --- | --- |
| **A Structuring** | Collect input + KB -> numbered PRD draft | Deliver Markdown/HTML draft + revision log |
| **B Submission** | After user/Leader confirms the scope -> `multica-pm-artifact-publish` | Return the PRD link (Git version: file link on the deploy branch) |

Revision after review: go back to phase A to change the content -> call publish again to **update** (not to create a duplicate). See publish skill Workflow B.

## Step 0.5 — Knowledge base (two ways of use)

Call `multica-platform-knowledge-base` -> `kb_ask.py` (SSH/curl forbidden).

| Information type | May it go into the PRD | Where to write it |
| --- | --- | --- |
| Terms, module boundaries, historical background | **Reference** | Background / revision log / OP- citations |
| Menu paths, permission names, field aliases (relevant to the current requirement) | **Should be used** | Executable wording of FR- / BR- / AC- |
| Historical rules, other systems' definitions, fields the current requirement does not mention | **Forbidden as new FR/AC** | Background only; on conflict the current Issue wins |

Knowledge base unavailable: mark "knowledge base unavailable"; this **does not block** structuring; never invent business rules. For stopping a round on timeout see the platform KB SKILL.

## Process

1. Identify the business goal (G- + KPI-)
2. User roles / permissions
3. Scope (in / out) and non-goals
4. Constraints (compatibility / performance / security / time)
5. Acceptance criteria (AC-, testable)
6. Ambiguities -> OP- open-questions list
7. Dependencies and risks (RISK-)

## Requirement structure

Section baseline: `scripts/templates/prd-template.md` of `multica-platform-confluence`:

| Section | Numbering |
| --- | --- |
| One-sentence definition, background | — |
| Goals and success criteria | G- + KPI- |
| User stories | U- |
| Functional requirements | FR- |
| Business rules | BR- |
| Acceptance criteria | AC- |
| Open questions | OP- |
| Risks | RISK- |

A formal PRD contains at least: one-sentence definition, background, G-/KPI-, users and permissions, scope, FR-/BR-/AC-, field definitions, empty / error / no-permission states, RISK-/OP-, and the **revision log**.

## Output

- **Goals (G-)**, **scope**, **non-goals**
- **Acceptance criteria (AC-)**, **constraints**, **dependencies**
- **Open questions (OP-)**, **risks (RISK-)**
- **Revision log**: version number, date, change summary (must be bumped after every review revision)

## Rule

If an ambiguity would materially affect the implementation -> **BLOCKED** -> state what is missing and who should provide it; ask only 1 most critical question.

## Revision after review (with multica-review-product)

| Review verdict | PM action |
| --- | --- |
| **FAIL** | Revise the numbered PRD items per the change checklist -> update the revision log -> `multica-pm-artifact-publish` **Workflow B update** -> ask ProductReviewer to re-review |
| **PASS** | Hand to the Leader for `multica-verification`; unclosed OP- items still must not enter development |

ProductReviewer **only reviews, never edits**; the PM performs the revision after the user/Leader authorizes "revise per review".

## Handoff

```text
1. multica-pm-requirement-spec   — structure the PRD (this skill)
2. multica-pm-artifact-publish — land / update the PRD (Git version: docs/prd/<ISSUE-KEY>.md); optional DingTalk notification
```

## Why it works

Requirement ambiguity is amplified downstream. Numbering + the OP- list + KB background (without expanding scope) make the PRD reviewable and testable; content is decoupled from the platform, so after a review it can be updated a second time without creating a duplicate Story.
