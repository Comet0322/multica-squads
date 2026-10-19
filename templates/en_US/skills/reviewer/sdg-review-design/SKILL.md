---
name: sdg-review-design
description: Checklist for reviewing one design file against its PRD.
---

# Review: DESIGN

1. Every PRD `AC-n` has a traceability line to a part of the design.
2. It fits the repo: named files, modules and functions exist on the default branch or are marked new; for an empty repo a directory layout is given.
3. It says whether the change has a user interface, and splits the work into backend and frontend parts accordingly.
4. A simpler alternative was considered and the reason for rejecting it is stated; failure cases, error handling and an executable test plan are stated.
5. Risks have a mitigation; unknowns are `TBD` under Open questions.
