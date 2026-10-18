# Tester Skill Cross-Reference

> Consolidated from `acceptance-verifier-squad/INVENTORY.md`. Multica **mounts skills by name**; for paths see the categorized directories under `templates/skills/`.  
> **Do not** hardcode old `*-squad` names or local absolute paths in Agent instructions; reference only `multica-*` skill names.

## Mount order (@Tester)

1. **`multica-test-orchestration`** - cross-stage orchestration (preferred)
2. Read the sub-skill for each stage (see table below)
3. Platform / Reviewer skills are declared by the sub-skills via `metadata.orchestrates`

## Stage -> Skill (mapping to former squads)

| Stage | Current skill | Former squad | Notes |
| --- | --- | --- | --- |
| Orchestration | `multica-test-orchestration` | acceptance-verifier-squad | Routing, gates, skill-inventory |
| T1 design | `multica-test-t1-design` | test-case-generator-squad + ac-design-trace-squad | Content + scripts combined |
| T1 review | `multica-review-test` | test-case-review-squad | reviewer/; reviews only, never imports |
| T1 KB | Team knowledge base (optional) | Team knowledge-base Q&A (optional platform skill) | platform/ |
| T1/T2 Apifox write | `multica-platform-apifox` | apifox-test-case-supplement-squad | Scenario supplementation, not a T3 batch run |
| T2 | `multica-test-t2-coverage` | ac-coverage-t2-squad | Gap assessment |
| T3 UI | `multica-test-t3-ui-automation` | functional-ui-auto-squad | pytest UI |
| T3 API | `multica-test-t3-api-automation` | software-development | Orchestration + validation |
| T3 batch-run CLI | `multica-platform-apifox` | (former automation CLI) | `run_apifox.py` |

## Former squad files -> current references (T1 / Apifox / Review)

| Former path (generator / review / apifox) | Current path |
| --- | --- |
| `test-case-generator-squad/SKILL.md` Step 0.5 | `multica-test-t1-design/references/generation-workflow.md` |
| `…/SKILL.md` Output Format | `…/references/output-format.md` |
| `…/SKILL.md` executability/permissions | `…/references/executability-and-permissions.md` |
| `…/SKILL.md` dimensions/scale | `…/references/coverage-dimensions.md` |
| `…/references/coverage-checklist.md` | `…/references/coverage-checklist.md` (same version) |
| `…/references/test-case-template.md` | `…/references/test-case-template.md` (same version) |
| `…/references/data-sources.md` | `…/references/data-sources.md` + platform skills |
| `…/MULTICA.md` | `…/references/agent-instructions.md` |
| `…/scripts/*` | `…/scripts/*` (fetch moved to platform) |
| `ac-design-trace-squad/SKILL.md` | `…/references/design-trace.md` |
| `test-case-review-squad/checklist.md` | `multica-review-test/checklist.md` |
| `test-case-review-squad/AGENT_INSTRUCTIONS.md` | `multica-review-test/references/agent-instructions.md` |
| `apifox-test-case-supplement-squad/SKILL.md` | `multica-platform-apifox/references/supplement-workflow.md` |
| `…/reference.md` | `…/references/reference.md` |
| `…/MULTICA.md` | `…/references/agent-instructions.md` |
| `…/CHANGELOG.md` | `…/references/CHANGELOG.md` |
| Team knowledge-base Q&A (optional platform skill) `/SKILL.md` | Team knowledge base (optional) `/SKILL.md` |

## Key T1 references

| File | Purpose |
| --- | --- |
| `multica-test-t1-design/references/generation-workflow.md` | Two phases, go-ahead, test-management platform, Step 0.5 |
| `multica-test-t1-design/references/output-format.md` | JSON 1:1, coverage self-check table |
| `multica-test-t1-design/references/executability-and-permissions.md` | Permission identification order, executability self-check |
| `multica-test-t1-design/references/coverage-dimensions.md` | Dimensions and scale |
| `multica-test-t1-design/references/multimodal-content.md` | HTML/images |
| `multica-review-test/checklist.md` | Review checklist items |

## Do not mix

- T1 import: **only** `multica-test-t1-design/scripts/import_to_tracker.py` (run by Tester)
- T1 review: **only** `multica-review-test` (TestReviewer; never imports)
- T3 UI: **do not** use xmind-ui-automation / playwright.git
- Apifox base URL: enterprise self-hosted (see platform-apifox config), not app.apifox.com
- **Do not** mount old squad names without the `multica-` prefix (`test-case-generator-squad`, etc.)

## Agent instruction entry points

| Skill | Copyable instructions |
| --- | --- |
| Orchestration | `multica-test-orchestration/references/agent-instructions.md` |
| T1 | `multica-test-t1-design/references/agent-instructions.md` |
| Review | `multica-review-test/references/agent-instructions.md` |
| Apifox supplement | `multica-platform-apifox/references/agent-instructions.md` + `supplement-workflow.md` |
