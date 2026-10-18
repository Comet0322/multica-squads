# Spec template (the single source of the Issue / spec format)

Every requirement that enters the squad uses exactly this layout, whether a human fills it in or the ProductManager writes it after a chat. `scripts/check_spec.py` enforces it. Do not rename the `##` headings.

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

## Rules `check_spec.py` enforces

| # | Rule |
| --- | --- |
| 1 | Exactly one Issue Source box is ticked. External link: a URL and a one-line summary are present and the other sections may be omitted. |
| 2 | At least one involved end is ticked (Design / Frontend / Backend / Testing). |
| 3 | Self-contained: Background, Goal, Scope "Changes", Non-goals and Acceptance Criteria are non-empty. |
| 4 | Acceptance criteria are numbered `AC-1`, `AC-2`, ... without gaps, each with a real sentence. |
| 5 | No vague words in an AC (`etc.`, `and so on`, `appropriate`, `relevant`, `as needed`, `user-friendly`, `TBD`, `TODO`, `a bit`). |
| 6 | Every `OP-n` is marked `[resolved: ...]` (the human's answer, or a fact with its source such as `MULTICA.md §6`) or `[accepted by human: ...]` (only after the human said so in the chat); an open question blocks creation. |

Numbering used across the squad: G- goals, FR- functional requirements, BR- business rules, AC- acceptance criteria, OP- open questions, RISK- risks.
