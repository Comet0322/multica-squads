---
name: sdg-review-code
description: The checklist a BACKEND or FRONTEND delivery is judged by. Backend and Frontend build to it; the Reviewer reviews with it.
---

# CODE

## Checklist

1. It implements its part of the design (the files tagged backend, or frontend) and nothing the design does not ask for.
2. It changes only files of its part, all listed in Path.
3. It has tests for what it builds, and its Test command passes.
4. The design's failure cases are handled as the design says.
5. No secrets, credentials or machine-specific paths in the code; names and structure are readable.
