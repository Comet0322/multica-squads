# Coverage Dimensions and Scale Judgment

> Consolidated from `test-case-generator-squad` Step 1–2. Works together with [`coverage-checklist.md`](coverage-checklist.md).

## Dimension selection (per module)

| Dimension | When required | When it can be skipped |
| --- | --- | --- |
| **Full scenario** | There are business function paths | Never |
| **Boundary scenario** | There is input/filter/numeric/upload | Display-only with no input restrictions |
| **Page check** | There is a new page/dialog/UI component | Pure backend, no UI change |

## Scaling by requirement size

| Size | Characteristics | Coverage strategy |
| --- | --- | --- |
| **Small** | 1–2 function points / single-page change | Core normal flow + key exceptions; non-essential boundary/UI may be skipped |
| **Medium** | 3–5 function points / includes forms | Full + necessary boundaries; UI as needed |
| **Large** | 5+ function points / multiple modules / complex states | Full + boundary + UI, nothing missed |

**No limit on case count** — the standard is full coverage of the current requirement: small requirements do not sprawl, large requirements do not leave gaps.

**Auto-dedup during generation:** the same module, same scenario and same operation path is generated only once.

**Merge and split:** equivalent negative cases may be merged (list numbered samples in the expected result); key boundaries or standalone PRD risk items should stand alone. See [`generation-workflow.md`](generation-workflow.md).

## Full-scenario checklist

Normal / branch / exception / state transition / permission / data linkage / combination / concurrency — every function point mentioned in the requirement needs at least one positive and one negative case.

## Boundary-scenario checklist

Numeric / string / list / enum / time / format / required / uniqueness / file / pagination — each input control needs boundary values (upper/lower/beyond boundary).

## Page check (qualitative, not pixel-level)

Element completeness, layout consistency, style, interaction states, responsiveness, copy text, empty/loading/error states. **Skip** exact px, HEX, corner radius, etc. (left to UI walkthrough).

## Module coverage matrix (must be listed before generation)

```text
========================================
Module: {module name}
========================================
[Coverage matrix]
  ┌ Full scenario: …
  ┌ Boundary scenario: … (or "skipped for this module")
  ┌ Page check: … (or "skipped for this module")

--- Cases ---
(case details are output afterwards)
```

The matrix is written into the "Module coverage" section of the coverage report.

## API cases (local)

- JSON contains `"api"` alongside `"functional"`
- Also save `test_cases_api.json` (api array only)
- **Do not** import into JIRA / XMind / test-management platform
- Executable scenarios -> `multica-platform-apifox`

## XMind rules

```bash
python scripts/generate_xmind.py \
  --input ./data/test_cases.json \
  --output ./data/test_cases_{JIRA_KEY}.xmind \
  --project {PREFIX}
```

- File name must be `test_cases_{JIRA_KEY}.xmind`
- **Do not** delete xmind files of other Keys
- Functional cases only; api is excluded
