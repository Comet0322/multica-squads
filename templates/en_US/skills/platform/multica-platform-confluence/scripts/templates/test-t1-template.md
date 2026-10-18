# T1 Test Cases — {ISSUE-KEY}

| Field | Value |
| --- | --- |
| Author | @Tester |
| Created | {YYYY-MM-DD} |
| Version | v1.0 |
| Status | Draft / Reviewed / Imported to JIRA |
| JIRA | {ISSUE-KEY} |
| Upstream PRD | {Confluence PRD / Issue Hub link} |
| Upstream design | {Figma / design link, or N/A} |
| API contract | {Confluence contract link, or N/A} |

## Traceability matrix

| AC- | Design/page | CASE-ID | Priority | Automation |
| --- | --- | --- | --- | --- |
| AC-1 | | CASE-001 | P0 | UI e2e / Apifox / manual |

## Functional cases (body · primary copy in Confluence)

> T1/T2 **do not generate XMind**; after review passes, a human's go-ahead command triggers the XMind export for import into JIRA.

### CASE-001 — {Title}

| Field | Value |
| --- | --- |
| Module | {module/path} |
| Priority | P0 / P1 / P2 |
| Preconditions | |
| Permissions | |

**Steps and expected results** (equal length):

| # | Step | Expected result |
| --- | --- | --- |
| 1 | | |
| 2 | | |

**Related AC-**: AC-1

---

### CASE-002 — {Title}

(Same structure as above; one section per case)

## API scenarios (Apifox · not written to JIRA)

| Item | Value |
| --- | --- |
| Contract source | {Confluence api-contract link} |
| Apifox project ID | |
| AI branch | ai/{ISSUE-KEY}-openapi-{date} |
| Endpoints / scenarios added | {path + scenario summary, or N/A} |
| Git manifest | tests/api/{ISSUE-KEY}/manifest.json |

## UI automation plan (committed from T2 onward)

| CASE-ID | tests/e2e file | Status |
| --- | --- | --- |
| CASE-001 | test_case_001.py | To be written in T2 / exists |

## Coverage self-check

- [ ] Positive main path
- [ ] Boundaries and exceptions
- [ ] Permission / no-permission states
- [ ] Empty state (when applicable)
- [ ] One-to-one with AC-

**Gap notes**: (write "None" if there are none)

## Revision history

| Version | Date | Description |
| --- | --- | --- |
| v1.0 | | Initial draft |
