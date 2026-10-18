# Frontend Review Checklist

Use together with [`review-workflow.md`](review-workflow.md). Read-only review by default; **Must Fix** causes FAIL, **Suggest** / **Nit** never cause FAIL on their own.

## 0. Materials and scope

- [ ] Read the Issue, latest comments and the implementer's completion note
- [ ] Read the impl-spec, UI and API contract (links from the Leader's dispatch)
- [ ] The diff matches the changed-file list and covers the issue goal
- [ ] The review is based on code in the **project repository**, not the Multica task temp directory

## 1. Requirements and user flow

- [ ] The implementation meets the issue's user goal and every AC-
- [ ] UI, API and state form a **complete user flow** (not isolated pages)
- [ ] No unauthorized expansion of product scope or business definitions

## 2. Interaction and UI states

- [ ] **loading** - async requests give loading feedback
- [ ] **empty** - empty data has an explanation or guidance
- [ ] **error** - errors are understandable and retryable where needed
- [ ] **disabled / permission** - no-permission or unavailable states are correct
- [ ] **responsive** - no obvious layout breakage (if the PRD/design requires it)
- [ ] Forms: validation, submitting state and **duplicate-submit prevention** are reasonable

## 3. Lists and data

- [ ] List **keys** are stable and unique
- [ ] Pagination, filtering and refresh logic are correct and do not lose state
- [ ] Fields, enums and pagination parameters match the API contract

## 4. TypeScript and component boundaries

- [ ] Types are clear; no abuse of `any`
- [ ] Props / Emits / Expose / Slots types are explicit
- [ ] **No direct HTTP calls inside components** (go through the project's api client / hooks)
- [ ] Side effects (subscriptions, timers, listeners) are cleaned up; no leak risk

## 5. Consistency with project patterns

- [ ] Reuses the project's existing components, hooks, store, api client, types, styles and utilities
- [ ] No **unrelated refactoring** and no widened change scope
- [ ] Follows project directory and naming conventions (if documented)

## 6. Impact surface

- [ ] Whether shared-component changes affect other pages/teams
- [ ] Whether routing, navigation, permissions or caching were changed unexpectedly
- [ ] Regression risk for core flows (login, ordering, approval, etc.)

## 7. API contract

- [ ] Request parameters, response structure and error-code handling align with the contract
- [ ] Error UX (toast / inline / retry) is reasonable
- [ ] Consistent with the impl-spec

## 8. Testing and verification

- [ ] Key interaction paths have unit tests or traceable manual verification notes
- [ ] No "useless tests" (always green, mock-only with no meaningful assertions)
- [ ] The implementer's verification note is credible enough; if not, record it under **residual risks**

## 9. Accessibility and performance (mostly Suggest; Must Fix when severe)

- [ ] No obvious a11y blockers (focus, labels, state conveyed by color only, etc.)
- [ ] No obvious performance issues (huge lists without virtualization, duplicate requests, etc.), as the issue requires

## 10. Pre-output self-check

- [ ] Must Fix / Suggest / Nit are distinguished
- [ ] Every Must Fix includes a location and a fix
- [ ] Stated which checks/tests were run, or why they could not be run
- [ ] Listed the items that could not be verified
- [ ] Even on PASS, wrote the key points checked and residual risks
