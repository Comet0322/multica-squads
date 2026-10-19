---
name: sdg-review-test
description: Checklist for reviewing one TEST delivery against the PRD.
---

# Review: TEST

1. Every PRD `AC-n` has at least one test, and `AC coverage` matches the tests in the files.
2. Each test asserts the behaviour its AC describes, not just that code runs.
3. The design's failure cases are tested.
4. Tests are deterministic: no network, no real user files, temporary directories only.
