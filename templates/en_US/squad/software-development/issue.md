# Issue Template

> Copy into a new Issue, fill it in, then hand it to the Squad.

```markdown
# Feature

## Issue source (required, pick one)
<!-- Decides how much to fill in. With "External link", only fill the link + summary + affected ends below; skip the other sections and reference the KEY in Notes. Full requirements live in Jira/Tapd etc., the Squad pulls them by KEY -->
- [ ] External link (lightweight): only fill "link / one-line summary / affected ends"; other sections omitted
      - Link: https://jira.example.com/browse/<ISSUE-KEY>
      - Summary: <!-- one line on what to do -->
- [ ] Fully self-contained (default): this Issue is the requirement; fill in all sections below

## Background
<!-- Why are we doing this? -->

## Goal
<!-- What problem should this feature solve? -->

## Scope
<!-- The Leader routes by this: ends not checked get no role; their artifacts are skipped -->
- Affected ends (check):
  - [ ] Design (needs Architect to propose a plan)
  - [ ] Frontend (needs FrontendDev)
  - [ ] Backend (needs BackendDev + API contract)
  - [ ] Testing (needs Tester for functional/API cases and test report)
- What to change: <!-- What should change? -->

## Non-goals
<!-- What explicitly won't be done? -->

## Acceptance criteria (must be testable)
- [ ]
- [ ]
- [ ]

## References
<!-- Docs, Issues, screenshots, code locations -->

## Notes
<!-- Anything else the squad needs to know -->
```

---

## Why it's written this way

- **The "affected ends" in the scope is the routing input**: the Leader's G0 uses it to decide which roles to dispatch. Missing or vague scope → G0 FAIL, instead of the Leader guessing.
- **Goal / Scope / Non-goals separated**: prevents agents from freewheeling and expanding the scope.
- **"Source: pick one" lightens link-type Issues**: when the source is Jira/Tapd, full requirements live externally; this Issue only needs "link + affected ends + one-line summary" to drive G0 routing and gating. With "fully self-contained", prioritize Background / Goal / Scope / Non-goals / Acceptance criteria, and add References / Notes as needed. Both forms share the same `<ISSUE-KEY>`; the gate system is unchanged.
- **An Issue is a requirement contract, not an implementation blueprint**: the person filing it is usually a PM (one Issue = one requirement). The template keeps only requirement elements (why / what / affected ends / non-goals / testable AC); technical context, constraints, traceability matrix, verification, and Git branch are produced by the Squad during the run, not front-loaded onto the PM.

## Common failure

- Only writing "please build this feature for me" → the squad either guesses or gets stuck at G0.
- Not checking "affected ends" → the Leader doesn't know whether to dispatch Frontend / Backend, and the flow runs as full-stack by default.
- Writing requirement details into Agent Instructions instead of the Issue → those instructions are dead the moment the task changes.
