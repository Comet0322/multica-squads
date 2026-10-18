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
  - [ ] Design (needs Architect)
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

- **"Involved ends" in Scope is the routing input**: Leader's G0 uses it to decide which roles to dispatch. Missing or vague scope → G0 FAIL, not a guess.
- **Goal / Scope / Non-goals separated**: prevents Agents from freely expanding scope.
- **Acceptance Criteria must be testable**: without testable criteria, gating can't run (multica-verification skill has nothing to check) and the whole gate system fails. This Starter adds dedicated Reviewer professional review on top, but review equally depends on clear, testable acceptance as its baseline.
- **"Source: pick one" lightens link-type Issues**: when the source is Jira/Tapd, full requirements live externally; this Issue only needs "link + involved ends + one-line summary" to drive G0 routing and gating. Both forms share the same `<ISSUE-KEY>`; gate system unchanged.
- **Issue is a requirements contract, not an implementation blueprint**: the Issue author is usually a PM (one Issue = one requirement). The template keeps only requirement essentials (why / what / involved ends / non-goals / testable acceptance); technical context, constraints, traceability, verification, Git branches are produced by the Squad at runtime—not pre-loaded as PM burden.

## Common failures

- Only "help me build this feature" → Squad either guesses or stalls at G0.
- Not checking "involved ends" → Leader doesn't know whether to dispatch Frontend / Backend; flow defaults to full-stack.
- Putting requirement detail into Agent Instructions instead of the Issue → those instructions become invalid for the next task.
