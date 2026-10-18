# PRD Review Report Template

After finishing, ProductReviewer outputs using this template and **reports to the Leader**. Professional English; keep terms such as PRD, AC, FR, BR as is; short and actionable; do not paste large blocks of the original.

```markdown
## PRD Review Report

**Document**: [name / Confluence or JIRA link]
**Issue**: [Multica Issue or Story Key]

**Verdict**: PASS / FAIL / BLOCKED
**Value judgment**: Worth doing / Not worth doing / To be decided
**Logic judgment**: Logically closed / Has gaps / Inconsistent

### 1. Value assessment summary
(3-5 key points)

### 2. Logical closure check

| Check item | Verdict | Notes |
| --- | --- | --- |
| Goal - solution - acceptance chain | ✅ / ❌ / ⚠️ | |
| Roles and permissions | ✅ / ❌ / ⚠️ | |
| Main flow and exception flows | ✅ / ❌ / ⚠️ | |
| Business rule (BR-) consistency | ✅ / ❌ / ⚠️ | |
| Data definitions | ✅ / ❌ / ⚠️ | |
| Scope boundary | ✅ / ❌ / ⚠️ | |

### 3. Issue list

| ID | Level | Type | Description | PRD location | Recommendation |
| --- | --- | --- | --- | --- | --- |
| Q-001 | Must Fix / Suggest / Nit | Value / Logic / Clarity | | G-/FR-/AC- or section | |

(Must Fix = FAIL-blocking items; Suggest/Nit are non-blocking)

### 4. OP- and items to confirm
- OP- blocking development: ...
- Non-blocking OP-: ...

### 5. Knowledge base / historical reference (if used)
- Operation/term check: ...
- Rule-extrapolation check: none / yes (explain; state clearly when it is **not** treated as a PM defect)

### 6. Suggested next steps
- FAIL: Leader assigns @ProductManager to revise the spec -> publish Workflow B -> re-review
- PASS: report to the Leader; **development still must not start while OP- items are open**; wait for multica-verification
- BLOCKED: list the materials the Leader/human must supply

### 7. Re-review check (re-review rounds)
Versus the previous round's Must Fix: X resolved / Y unresolved  
Round: N / 3 (BLOCKED does not count as a FAIL round)
```

## Minimum requirements on PASS

Even on PASS, you must still fill in:

- Key points checked (at least 1 each for value / logic / clarity)
- Residual Suggest items or OP- risks (write "none" if there are none)

## Must not appear in the report

- "Ready for development / can be scheduled" (a professional review PASS != G1)
- @ProductManager or member mentions (the Leader dispatches)
- Creating/updating JIRA, splitting subtasks
