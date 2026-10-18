# Test Case Review - Detailed Checklist

Use together with `SKILL.md`; tick as needed, no need for a long explanation on every item.

## 0. Material sources (any one is enough)

- [ ] Functional case JSON (`jira_key` + `functional`), or
- [ ] XMind: `test_cases_{JIRA_KEY}.xmind` (including the Issue attachment), or
- [ ] An already imported JIRA / test management platform case set (steps + expected results)
- [ ] Requirement basis: Jira Key/link or collected AC
- [ ] Case source and requirement basis **both** missing -> verdict Block

## 1. Deliverables and gates

- [ ] A functional case JSON exists (with `jira_key`, `functional`)
- [ ] `test_cases_{JIRA_KEY}.xmind` exists, with a Key matching the JSON
- [ ] A coverage report or equivalent note exists (weak constraint; a missing one is Minor unless the user requires it)
- [ ] The artifact is declared pending review; not imported into Jira during the review flow
- [ ] API cases, if any: local only; not in the XMind functional tree

## 2. JSON structure

- [ ] Each case: `case_id`, `module`, `title`, `preconditions`, `steps`, `expected_results`, `priority`, `coverage_dimension`
- [ ] `len(steps) == len(expected_results)` and both sides are non-empty
- [ ] When an expectation has several verification points, organize them with `1)` `2)` while still being one `expected_results` element
- [ ] `module` is a `/` path (e.g. `Overview Board/New Order Stage/Stage Switch`)
- [ ] Hierarchy semantics: system prefix <-> requirement name <-> business domain/module is sensible, nothing misplaced

## 3. Prohibited items (text)

- [ ] No Confluence wiki residue: `{LQ}` `{RQ}` `{color}` `{noformat}` etc.
- [ ] No `[to be added]` `[TBD]` `[placeholder]` `[missing Figma...]` etc.
- [ ] No unresolved literal permission placeholders such as `XXX` / "some permission"
- [ ] No hard-coded personal accounts, passwords or private phone numbers (except an acceptance whitelist in the requirement itself, still without passwords)

## 4. Priority

- [ ] No `P0`
- [ ] Exception / boundary -> P3
- [ ] Core main acceptance path -> P1
- [ ] Everything else normal / page checks, etc. -> P2
- [ ] No "core marked P3" or "pure boundary marked P1"

## 5. Requirement alignment (the current Jira prevails)

- [ ] Every AC / key rule-table row has a corresponding case or a reasonably explained uncovered
- [ ] No 138 / Confluence historical **rules** written into expected as acceptance
- [ ] **Entry / permission / wording aliases** from the knowledge base appear in the steps of relevant cases (within the current requirement scope)
- [ ] No fields / branches / states that the current requirement does not describe are written up as test points
- [ ] On conflict the current AC prevails; the difference may be recorded in the report

## 6. Executability

- [ ] Preconditions: permission semantics filled in for the **current system** (not empty boilerplate)
- [ ] Steps contain real menus / entries or an explicit backend trigger method (never invent menus)
- [ ] Waiting is stated where loading is needed; test-data creation has aliases and key field values
- [ ] Expected results are concrete and decidable; no "should", "may", "appropriate"
- [ ] Merging Action+Verify is reasonable; not mechanically split into steps with empty expectations

## 7. Coverage dimensions (by requirement size; not all three dimensions are mandatory)

- [ ] Business paths present -> full scenario coverage of the main path and the in-requirement branches / exceptions
- [ ] Inputs / limits present -> necessary boundaries (small requirements may be trimmed, but key numeric boundaries must not be dropped)
- [ ] New page / new dialog present -> page checks use qualitative expectations (do not review px / color values)
- [ ] The coverage report matches the real cases; no fake coverage

## 8. Sampling strategy (consistent with SKILL)

| Size | Strategy |
| --- | --- |
| <=10 cases | **Review all** (P1/P2/P3 each one) |
| 11-30 cases | **All P1** + **at least 50%** of P2/P3 |
| >30 cases | **All P1** + **at least 1 P2 and 1 P3 per module** + duplicate check |

P2/P3 samples must cover different modules and different coverage_dimension values; on finding a Major, widen the sampling range.

## 9. Re-review after revision

After the user authorizes revision:

- [ ] Change only the problem items; do not widen the scope in passing
- [ ] Regenerate `test_cases_{KEY}.xmind` (do not delete other requirements' XMind)
- [ ] Run the review again; still no import

## 10. Verdict and import boundary

- [ ] Exactly one verdict: **Block** | **Revise** | **Pass** (consistent with the SKILL output template)
- [ ] **Pass != import authorization** - the footer only prompts a human to confirm and then tell the Tester "review passed, import into JIRA"
- [ ] Block/Revise: the import recommendation reads "import forbidden; revise and regenerate XMind first"
- [ ] Even if the user tells this Agent "import into JIRA" -> still do not run the import; ask the Tester to handle it
- [ ] When reviewing a case set already imported to the test management platform: check steps/expected results against the current AC; a local JSON file path is not required
