# software-development-reviewed

Extends `software-development` by giving **every regular producing role except Leader and DevOps** a **dedicated Reviewer**, forming a two-layer quality assurance: "generic gate + professional artifact review".

## When to use

- You need more than "the process completed"—you need artifacts that are themselves professional and defensible.
- The team holds high professional bar for architecture design, UI, requirements, frontend/backend implementation, and test artifacts.
- You want professional review opinions **independent of the implementer**, unified and dispatched by the Leader in a fix-and-re-review loop.

If you only want the lightweight flow, use `software-development` (just the Leader-triggered multica-verification generic gate).

## Discussing the spec first (optional)

You do not have to write the Issue yourself: open a chat with the **ProductManager** agent, describe the idea and answer its questions one by one. When you say "create it", it files a fully self-contained Issue assigned to this squad (see the Chat mode section of `multica-pm-requirement-spec`); the Leader then starts at G0 and skips the PRD stage because the Issue already is the requirement.

## Difference from software-development

| Dimension | software-development | software-development-reviewed |
| --- | --- | --- |
| Gate layers | 1: Leader generic gate (multica-verification) | 2: generic gate + dedicated Reviewer professional review |
| Reviewer role | G1 business review only (single point) | Dedicated Reviewer per role, per-artifact professional review |
| Review trigger | Leader-triggered | Leader dispatches after generic gate PASS |
| Review conclusion flow | Directly into design gate | Reports to Leader → Leader dispatches author fix → re-review (≤3 rounds) |
| Use case | General collaboration | High professional bar |

## Role → dedicated Reviewer mapping

| Producing role | Dedicated Reviewer | Review skill | Review focus |
| --- | --- | --- | --- |
| @ProductManager (PRD) | @ProductReviewer | multica-review-product | scope/goal/acceptance clear & testable, no missing critical constraints |
| @Architect (design) | @ArchReviewer | multica-review-architect | soundness, extensibility, acceptance alignment, tech risk |
| @Designer (UI) | @DesignReviewer | multica-review-designer | interaction soundness, accessibility, design-system/acceptance consistency |
| @FrontendDev (frontend) | @FrontendReviewer | multica-review-frontend | fit to UI/API contract, component quality, unit tests reasonable & sufficient |
| @BackendDev (backend + API contract) | @BackendReviewer | multica-review-backend | contract quality, design fit, error handling, unit tests reasonable & sufficient |
| @Tester (cases / report) | @TestReviewer | multica-review-test | coverage depth, coverage doc reasonableness, line-by-line acceptance mapping |

> Leader and DevOps get **no** dedicated Reviewer: Leader is orchestrator (gate + review would share the same source); DevOps artifact is a deploy URL already covered by CI hard gate.

## How the two-layer gate runs

```
Producing role finishes artifact
   → Leader generic gate: multica-verification skill re-checks acceptance/process (only "correct?")
   → if PASS: dispatch matching dedicated Reviewer with multica-review-* skill for professional analysis (only "professional?")
       → if review PASS: artifact released, advance to next stage
       → if review FAIL: dedicated Reviewer outputs conclusion + fix list, reports to Leader
            → Leader dispatches the producing role to fix
            → after fix, re-review by same dedicated Reviewer
            → max 3 rounds; still FAIL at round 3 → escalate to human
   → if FAIL: return to author, counted as generic-gate FAIL (3 consecutive → escalate to human)
```

Either layer FAIL returns; **rounds counted independently but share the "3-strike cap"**.

## Key constraints

- Dedicated Reviewer **doesn't modify on the author's behalf**; only outputs conclusion + fix list and reports to Leader.
- Leader **must not substitute review conclusion for generic gate**, nor approve on the dedicated Reviewer's behalf.
- Dedicated Reviewer and producing role are **independent**; same artifact re-review must be by the same dedicated Reviewer.
- All other routing / stage-gate / evidence / failure / escalation rules are identical to `software-development`.

## Companion files

- `squad.md`: full Squad instructions (incl. two-layer gate and professional review sub-loop).
- `issue.md`: Issue template (same as software-development; no extra fields needed for review).
- Dedicated Reviewer Agents: `arch-reviewer` / `design-reviewer` / `product-reviewer` / `frontend-reviewer` / `backend-reviewer` / `test-reviewer`.
- Dedicated review Skills: `multica-review-architect` / `multica-review-designer` / `multica-review-product` / `multica-review-frontend` / `multica-review-backend` / `multica-review-test`.
