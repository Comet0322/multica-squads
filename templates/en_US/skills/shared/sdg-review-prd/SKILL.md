---
name: sdg-review-prd
description: The PRD template and the checklist it is judged by. The PM writes with it; the Reviewer reviews with it.
---

# PRD

## Template

Write `docs/prd/<ISSUE-KEY>.md` with exactly these headings, in this order. Keep it short: bullets, no filler prose. Leave nothing out: a heading with nothing to say gets the single line `none`.

```markdown
# PRD <ISSUE-KEY>
## Goal
## Scope
## Non-goals
## Acceptance criteria
- AC-1: <one statement a third party can check pass/fail>
## Open questions
- Q-1: <question the issue leaves open>
```

## Checklist

0. Headings exactly as the template, in order; every section filled or `none`.
1. Goal and scope are stated; non-goals are explicit.
2. Every `AC-n` is testable: a third party could say pass/fail from it.
3. Nothing contradicts the issue text; nothing is added that the issue did not ask for; nothing the issue leaves open is decided.
4. Every unknown is under Open questions; none is hidden in the text.
5. It is grounded in the repo: if the default branch has code, the PRD names what it touches; if it is empty or only has a README, the Goal says this is a new project.
