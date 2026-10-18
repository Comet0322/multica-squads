# JSON Output and Delivery Format (mandatory)

> Consolidated from `test-case-generator-squad` Output Format / Output Delivery / coverage self-check table. Works together with [`generation-workflow.md`](generation-workflow.md) and [`test-case-template.md`](test-case-template.md).

## JSON structure (`test_cases.json`)

**Mandatory:** the `steps` and `expected_results` **arrays must have exactly the same length (1:1)**; no auto-padding or placeholders. Validate after generation and abort with an error on mismatch.

> **Relation to the step-writing principle:** within a single step you may list several verification points in one `expected_results` element using `1)` `2)`; but **at the array level** each step still maps to exactly one expected result (one array element).

**API cases:** stored under the `"api"` key; also export `test_cases_api.json` as a local backup. They **do not take part** in JIRA / XMind / test-management-platform import.

```json
{
  "jira_key": "PROJ-123",
  "functional": [
    {
      "case_id": "TC-F-LOGIN-001",
      "module": "User Login",
      "coverage_dimension": "Full scenario",
      "title": "Verify login succeeds with correct username and password",
      "preconditions": ["Registered", "Login page opened"],
      "test_data": "user: test@c.com / pass: Abc@123456",
      "steps": ["Enter username", "Enter password", "Click Login"],
      "expected_results": ["Login succeeds and redirects to the home page"],
      "priority": "P1",
      "case_type": "Functional flow"
    }
  ],
  "api": [
    {
      "case_id": "TC-I-LOGIN-001",
      "module": "User Login",
      "coverage_dimension": "Full scenario",
      "title": "Verify POST /api/v1/login with correct parameters returns success"
    }
  ],
  "generated_summary": {
    "total": 25,
    "functional": 20,
    "api": 5
  }
}
```

### Field notes

| Field | Description |
| --- | --- |
| `jira_key` | Matches the XMind file name and the target Story for import |
| `coverage_dimension` | `Full scenario` / `Boundary scenario` / `Page check` |
| `priority` | P1 / P2 / P3; **P0 is forbidden** |
| `generated_summary` | The Phase A report must include total / functional / api |

---

## Output to the user (readable format)

1. **Output functional and API cases separately**
2. **Group by module**; within a module, order: Full scenario -> Boundary scenario -> Page check (show only the dimensions actually covered)
3. **Every module must start with a coverage matrix**:

```text
========================================
Module: {module name}
========================================
[Coverage matrix]
  ┌ Full scenario: {coverage list}
  ┌ Boundary scenario: {coverage list} (omit if not covered)
  ┌ Page check: {coverage list} (omit if not covered)

--- Cases ---
(case details)
```

---

## Output Delivery rules (six)

1. **Output functional and API cases separately**
2. **Group by module**; order by dimension within a module (show only dimensions actually covered)
3. **The coverage matrix must be output** — dimensions not covered are not shown
4. **When materials are insufficient** — missing Figma/API docs that cannot be obtained -> **do not** generate placeholder cases; report the blockers before generating. If expected results can be written clearly without the missing material, generate normally
5. **At the end of the generation phase, declare pending review** — Confluence is updated; state "not XMind / not imported to JIRA" and the import passphrase; **do not** claim it has been imported
6. **Report Issue Keys only at the end of the import phase** — output the case / case-set Keys and the link-validation result only after Step B completes

---

## Coverage self-check table (mandatory output in Phase A)

At the end of generation, check item by item and output (list only dimensions actually covered):

```text
=== Coverage Check Report ===

=== Historical context reference (Step 0.5) ===
  Confluence history: {list of titles/links, or "no hit"}
  Team knowledge base: {Q&A summary + cited sources, or "unavailable / no hit"}
  Usage note: background understanding only; case scope is strictly limited to the current requirement, with no extra test points introduced from reference sources

Module: User Login
  [✓] Full scenario — covered 6/6 business paths
  [✓] Boundary scenario — covered 8/10 boundary conditions (missing: concurrent login, token expiry)
  [✓] Page check — covered 5/5 page elements

Module: Product List
  [✓] Full scenario — covered 4/4 business paths
  [ ] Boundary scenario — covered 3/6 boundary conditions (missing: pagination boundary, sort boundary, filter combination)

=== Overall coverage ===
  [✓] Full scenarios covered in all modules
  [✓] Boundary scenarios covered in all modules (modules not covered are annotated with a reason)
  [✓] Page checks covered in all modules (modules not covered are annotated with a reason)
  [ ] Some dimensions not covered (list reasons)
```

May be used together with the Markdown coverage report template in [`generation-workflow.md`](generation-workflow.md); **the coverage self-check table must not be omitted**.
