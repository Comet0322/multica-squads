# T2 Coverage Assessment — {ISSUE-KEY}

| Field | Value |
| --- | --- |
| Author | @Tester |
| Created | {YYYY-MM-DD} |
| Version | v1.0 |
| JIRA | {ISSUE-KEY} |
| **T1 Confluence** | {t1-cases link — required} |
| G2 evidence | {SHA / MR link} |
| API contract | {link, or N/A} |

## Conclusion

**Assessment complete | Assessment BLOCKED** — {one sentence}

> T2 performs a static gap assessment only; it **does not generate XMind**.

## AC coverage

| AC- | T1 CASE | Implementation evidence | Status |
| --- | --- | --- | --- |
| AC-1 | CASE-001 | {file/MR} | Covered / False coverage / Gap |

## Supplementary cases (delta over T1 · body)

### SUP-001 — create — {Title}

(Same structure as a T1 CASE: steps / expected / AC-)

## Apifox supplement

| endpoint | Action | AI branch | Scenario ID |
| --- | --- | --- | --- |
| POST /api/... | Add scenario | ai/... | |

## Git automation updates

| Type | Path | Description |
| --- | --- | --- |
| UI e2e | tests/e2e/test_{case_id}.py | Added/modified |
| API manifest | tests/api/{ISSUE-KEY}/manifest.json | scenarioIds updated |

## Regression risks

- ...

## Revision history

| Version | Date | Description |
| --- | --- | --- |
| v1.0 | | Initial draft |
