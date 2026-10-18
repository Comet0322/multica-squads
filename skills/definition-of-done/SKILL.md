---
name: definition-of-done
description: What makes a ticket finished in a test-first squad
---

# Definition of done

A ticket is done only when all of these are true and evidenced:

- Every `AC#` and `I#` on its `Covers:` line has a test, and **that test has been seen to fail**. Which form of failure is owed is decided by one mechanical question — is the behaviour already present in the tree the test runs against?
  - **absent** → the test fails at `Red SHA`, on an assertion about behaviour, not a compile error or a missing file;
  - **present** → the test passes at `Red SHA`, and the evidence is a **throwaway mutation** that breaks the behaviour, with the pasted output of the test failing under it. The mutation is discarded, never committed.
  Behaviour is present for every `I#`, for an `AC#` an earlier ticket of this spec happened to deliver, and for an `AC#` on any reopened test stage once the implement stage has pushed. **Demanding a red run for behaviour that is present is a defect, not rigour**: it cannot exist, and asking for it is how a test that cannot fail, or no test at all, enters the suite.
- A criterion **a `**Spec correction**` retired** needs no test, and its existing tests may be deleted. The correction is the authority and it is durable; the `Retires:` line on a ticket is only the marker saying which ticket acts on it, so a ticket without that line still owes nothing for a retired number.
- Those tests pass now, and the whole suite passes.
- No test line that existed at `Red SHA` was changed or deleted, except for a criterion a `**Spec correction**` retired. Adding tests is allowed.
- The diff touches only files the spec's `Impact analysis` allows.
- Behaviour a user can see is documented by the ticket's docs stage, and that stage touched documentation files only.
- Build, vet and formatter show no **new** violations against the baseline the spec's `Repo intake` recorded. A repo that was already dirty is held to "nothing new", never to "clean" — tidying files the spec does not touch fails the scope check instead.
- The `Result` property is `PASS` and `Head SHA` names the commit it was given on.

Evidence is pasted command output. A report that contains none is incomplete, whatever it concludes.
