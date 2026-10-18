# Issue Template

> Copy into a new Issue, fill it in, then hand it to the Squad. This block is a verbatim copy of the canonical `references/spec-template.md` in the `multica-pm-requirement-spec` skill (the ProductManager's chat mode and `check_spec.py` use that file); do not edit it here — change the skill's template and re-copy.

```markdown
# Feature

## Issue Source (required, pick one)
<!-- Decides how deep this Issue is filled. For "external link", fill only the link + summary + involved ends. -->
- [ ] External system link (lightweight): only "link / one-line summary / involved ends"
      - Link: https://jira.example.com/browse/<ISSUE-KEY>
      - Summary: <!-- one line on what to do -->
- [ ] Fully self-contained (default): this Issue is the requirement; fill all sections below

## Background
<!-- Why do this? -->

## Goal
<!-- What problem does this solve? -->

## Scope
<!-- The Leader routes by this; ends that are not ticked are not dispatched and their artifacts are skipped -->
- Involved ends (check):
  - [ ] Design (needs Architect: technical design)
  - [ ] UI design (needs Designer: screens / interaction / visual)
  - [ ] Frontend (needs FrontendDev)
  - [ ] Backend (needs BackendDev + API contract)
  - [ ] Testing (needs Tester for functional/API cases and the test report)
- Changes: <!-- what should change? -->

## Non-goals
<!-- Explicitly what NOT to do -->

## Acceptance Criteria (must be testable)
- [ ] AC-1 <!-- one observable, testable statement -->
- [ ] AC-2

## Open Questions
<!-- Optional. Every item must be closed before the Issue is created. -->
- OP-1 <!-- question --> [resolved: the human's answer or a fact with its source] / [accepted by human: the risk the human accepted]

## References
<!-- docs, issues, screenshots, code locations -->

## Notes
<!-- other context the Squad needs -->
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
