---
name: definition-of-done
description: What makes a ticket finished in a test-first squad
---

# Definition of done

A ticket is done only when all of these are true and evidenced:

- Every AC on its `Covers:` line has a test, and that test was **seen to fail** at `Red SHA` for the right reason — an assertion about behaviour, not a compile error or a missing file.
- Those tests pass now, and the whole suite passes.
- No test line that existed at `Red SHA` was changed or deleted. Adding tests is allowed.
- The diff touches only files the spec's `Impact analysis` allows.
- Behaviour a user can see is documented by the ticket's docs stage, and that stage touched documentation files only.
- Build, vet and formatter are clean.
- The `Result` property is `PASS` and `Head SHA` names the commit it was given on.

Evidence is pasted command output. A report that contains none is incomplete, whatever it concludes.
