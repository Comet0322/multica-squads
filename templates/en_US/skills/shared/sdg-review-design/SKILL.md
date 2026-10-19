---
name: sdg-review-design
description: The design template and the checklist it is judged by. The Architect writes with it; the Reviewer reviews with it.
---

# DESIGN

## Template

Write `docs/design/<ISSUE-KEY>/design.md` with exactly these headings, in this order. Keep it short: bullets, no filler prose. Leave nothing out: a heading with nothing to say gets the single line `none`.

```markdown
# DESIGN <ISSUE-KEY>
## Approach
## User interface
- yes|no; if yes: what the frontend part covers
## Files
- <path> (new|changed) [backend|frontend|test]: <purpose>
## Traceability
- AC-1 -> <part of this design>
## Failure cases
- <case> -> <handling>
## Test plan
- <what is tested, by which command>
## Rejected alternative
- <simpler option> -> <why not>
## Risks
- <risk> -> <mitigation>
## Open questions
```

## Checklist

0. Headings exactly as the template, in order; every section filled or `none`.
1. Every PRD `AC-n` has a Traceability line.
2. Files fit the repo: listed files exist on the default branch or are marked new; every file is tagged backend, frontend or test, and the User interface section matches (no frontend files when it says no).
3. Failure cases, their handling and an executable test plan are stated.
4. A simpler alternative and the reason for rejecting it are stated; every risk has a mitigation.
5. Unknowns are under Open questions; nothing contradicts the PRD.
