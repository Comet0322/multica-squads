---
name: multica-review-test
description: "Test-artifact dedicated review framework: T1 case review (Block/Revise/Pass), T2 coverage-assessment re-check, and T3 report review (PASS/FAIL/BLOCKED). Outputs a conclusion and a fix list to Leader; mounted by TestReviewer."
---

> **[Git version]** This team's test artifacts live in the product repo: `docs/test/<ISSUE-KEY>/` (`t1-cases.md`, `t2-coverage.md`, `t3-report.md`) and `server/tests/`. Review those files; the parts below about Confluence / XMind / JIRA import do not apply. Focus on: every AC- has a case, and assertions really verify behavior (empty or always-true assertions are a Block).

# Test Artifact Professional Review (TestReviewer)

This skill provides a structured review of **test artifacts**. It is consolidated from **`test-case-review-squad`**.

## When to use

| Stage | Review target | Conclusion model |
| --- | --- | --- |
| **T1 Phase A** | `test_cases.json` + `test_cases_{KEY}.xmind` + design traceability | **Block / Revise / Pass** |
| **T2** | Output of `multica-test-t2-coverage` | Assessment complete / assessment BLOCKED |
| **T3** | Merged report + UI mapping + Apifox JSON | **PASS / FAIL / BLOCKED** (Leader gate) |

**Pass is not authorization to import into JIRA.** This role **never** calls `import_to_tracker.py`.

Agent instructions: [`references/agent-instructions.md`](references/agent-instructions.md).

---

## T1 review (Block / Revise / Pass)

### Inputs (missing primary deliverable -> Block)

| Required | Description |
| --- | --- |
| Functional case JSON | `jira_key` + `functional[]` |
| XMind | `test_cases_{JIRA_KEY}.xmind` |
| Requirement basis | Jira AC / collected PRD |

**Material sources (any one is enough to reconstruct `functional`; do not require a JSON path pasted in a comment):**

- Functional case JSON (`jira_key` + `functional`), or
- XMind: `test_cases_{JIRA_KEY}.xmind` (including the Issue attachment), or
- A case set already imported into JIRA / the test-management platform (steps + expected results)

**Both the case source and the requirement basis missing** -> Block; list the missing items and stop.

### Review order (no skipping steps)

1. **Lock the material** - Key matches the XMind file name; missing material -> Block
2. **Mechanical checks** - steps/expected have equal length; no P0; no wiki/TBD/missing-Figma/XXX placeholders; module uses `/` hierarchy
3. **Requirement alignment** - AC mapping table; false coverage; **two-way use rule** (operation-bucket content belongs in steps; rule-bucket content must not go into expected)
4. **Executability** - review **all P1**; **sample** P2/P3 (at least 1 P2 + 1 P3 per module, more for large modules); check entry path, permission semantics, test-data setup, verifiable expected results, priority P1/P2/P3
5. **Conclusion** - Block | Revise | Pass + the mandatory output template

For the detailed checklist see [`checklist.md`](checklist.md).

### Severity levels

| Level | Typical |
| --- | --- |
| **Critical** | Missing deliverable; broken structure; widespread placeholders; KB rules treated as AC; hard-coded passwords |
| **Major** | AC gap; false coverage; no entry path; P0 or priority disorder |
| **Minor** | Wordy titles; individual expected results that could match the UI copy more closely |

| Conclusion | Condition |
| --- | --- |
| **Block** | Critical, or insufficient material |
| **Revise** | No Critical, has Major |
| **Pass** | No Critical; Major = 0 (or accepted by the user in writing); Minor allowed |

On Revise with user authorization to modify -> edit the JSON -> `generate_xmind.py` from `multica-test-t1-design` -> **review one more round**; still no import.

### T1 output template (mandatory)

```markdown
# Case Review Report - {JIRA_KEY}

## Conclusion
**{Block|Revise|Pass}** - {one sentence}

## Material
- JSON: {path}
- XMind: {path}
- Requirement basis: {summary}
- Functional case count: {n}

## Critical / Major / Minor
- ...

## AC coverage mapping
| Acceptance point | Covering cases | Status |
| --- | --- | --- |

## Knowledge-base / history usage spot check
- Operation-bucket content written into steps: yes/no/partial
- Rule expansion: none/present

## Import recommendation
- Block/Revise: import forbidden; revise first and regenerate the XMind
- Pass: may be submitted for human confirmation; **this skill does not perform the import**. After confirmation, instruct Tester: "review passed, import into JIRA"
```

---

## T2 / T3 (Leader-gate style)

### T2 extra checks

- [ ] The 5 material items are traceable in comments
- [ ] Not written up as a "test report PASS/FAIL"
- [ ] "Implementation not delivered" and "cases to be added" are listed separately

### T3 extra checks

- [ ] G2.5 + deploy_url consistent
- [ ] UI: number of `functional` cases = number of pytest-collected tests
- [ ] Apifox report path exists
- [ ] Every AC in the merged report has evidence

### T2/T3 output format

```text
[Test Artifact Review] <stage T2|T3> <link or path>
Conclusion: PASS / FAIL / BLOCKED
Blocking items:
- ...
Suggestions:
- ...
Round: N / 3
```

---

## Boundaries

- Review only test artifacts, not implementation code
- Does not replace Leader's `multica-verification`
- Still FAIL at round 3 -> escalate to human
- **Even if** the user tells this Agent "import into JIRA", it is **forbidden** to run the import
