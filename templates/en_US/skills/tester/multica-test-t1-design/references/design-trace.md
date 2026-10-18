# AC <-> Design Traceability (T1 Step 1)

> Consolidated from `ac-design-trace-squad` (formerly a standalone skill). Complete this **before** writing cases; the traceability table goes into the "Design traceability" section of the T1 generation report.

## Inputs

- Issue / Jira acceptance criteria (prefer numbered AC-)
- Architect design: `docs/design/{KEY}/design.md` or a Confluence link (fetched via `multica-platform-jira` + `multica-platform-confluence`)

Design missing: state "no design, generated from AC only" in the report; do not invent design points.  
AC original text missing: BLOCKED on the traceability baseline; list the one-sentence scope the Issue has, and you may still list the design's §verification approach as "focus points (not AC)".

## Rules

- The acceptance denominator only counts the current Issue/PRD AC; in design but not in AC -> **focus points only, not acceptance**
- Conflict: Jira AC > linked PRD > design > knowledge base
- Operational information (entry points, permission names) may be given to case steps; rules must not be expanded into new AC

## Output template

```markdown
# Design Study Summary — {JIRA_KEY}

## Traceability table
| AC- | Design section | Test focus | Enters T1 acceptance |
|-----|----------------|------------|----------------------|
| AC-xx | §n | … | Yes/No (No = focus only) |

## In design but not in AC (must not be written as acceptance points)
- …

## Risks/boundaries (for T1/T2, not an automatic case expansion)
- …
```

## Why it is its own section

Lock the AC denominator before generating cases, so design documents or knowledge-base history are not expanded into extra acceptance points.
