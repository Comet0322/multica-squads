---
name: sdg-review-test
description: The checklist a TEST delivery is judged by. The Tester builds to it; the Reviewer reviews with it.
---

# TEST

## Checklist

1. Every PRD `AC-n` has at least one test whose name contains the AC id, and `AC coverage` matches the tests in the files.
2. Each test asserts the behaviour its AC describes, not just that code runs.
3. The design's failure cases are tested.
4. Tests are deterministic: no network, no real user files, temporary directories only.
5. The whole suite runs with the Test command; every failure is listed under `Open:` as `FAIL AC-n: <what happens>`.
