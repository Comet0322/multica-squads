---
name: sdg-review-ui
description: The UI spec template and the checklist it is judged by. The Designer writes with it; the Reviewer reviews with it.
---

# UI

## Template

Write `docs/design/<ISSUE-KEY>/ui.md` with exactly these headings, in this order. Keep it short: bullets, no filler prose. Leave nothing out: a heading with nothing to say gets the single line `none`.

```markdown
# UI <ISSUE-KEY>
## Screens
- <screen>: <purpose>; covers AC-n
## States
- <screen> empty|loading|error|success: <what is shown>
## Elements
- <element>: shows|sends <data> (from <design part>)
## Interactions and copy
- <user action> -> <result>; exact text in quotes
## Open questions
```

## Checklist

0. Headings exactly as the template, in order; every section filled or `none`.
1. Every user-facing `AC-n` maps to a screen.
2. Each screen has its empty, loading, error and success states.
3. Every element names the data it shows or sends, and that data exists in the design.
4. Interactions and copy are exact (labels, messages), not "e.g." or "something like".
5. Unknowns are under Open questions; nothing contradicts the PRD or the design.
