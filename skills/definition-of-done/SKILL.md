---
name: definition-of-done
description: What makes a ticket finished in a test-first squad
---

# Definition of done

A ticket is done only when all of these are true and evidenced:

- Every `AC#` and `I#` on its `Covers:` line has a test, and **that test has been seen to fail**. Which form of failure is owed is decided by one mechanical question — is the behaviour already present in the tree the test runs against?
  - **absent** → the test fails, on an assertion, when every non-test file the ticket changed is restored to `Base SHA` (the verifier does this itself) about behaviour, not a compile error or a missing file;
  - **present** → the test passes there too, and the evidence is a **throwaway mutation** that breaks the behaviour, with the pasted output of the test failing under it. The mutation is a diff the verifier applies itself, then discards; it is never committed.
  Behaviour is present for every `I#`, for an `AC#` an earlier ticket of this spec happened to deliver. **Demanding a red run for behaviour that is present is a defect, not rigour**: it cannot exist, and asking for it is how a test that cannot fail, or no test at all, enters the suite.
- A criterion **a `**Spec correction**` retired** needs no test, and its existing tests may be deleted. The correction is the authority and it is durable; the `Retires:` line on a ticket is only the marker saying which ticket acts on it, so a ticket without that line still owes nothing for a retired number.
- Those tests pass now, and the whole suite passes.
- No test line that existed at `Base SHA` was changed or deleted, unless a `**Spec correction**` (retiring or `Amends:` the criterion) or the owner's brief authorises it.
- The diff touches only files the spec's `Impact analysis` allows.
- Behaviour a user can see is documented by the ticket's docs stage, and that stage touched documentation files only.
- Build, vet and formatter show no **new** violations against the baseline the spec's `Repo intake` recorded. A repo that was already dirty is held to "nothing new", never to "clean" — tidying files the spec does not touch fails the scope check instead.
- The `Result` property is `PASS` and `Head SHA` names the commit it was given on.

Evidence is pasted command output. A report that contains none is incomplete, whatever it concludes.
