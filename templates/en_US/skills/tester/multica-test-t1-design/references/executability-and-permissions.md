# Executability and Permissions Spec (system-wide, mandatory)

> Consolidated from the `test-case-generator-squad` "Executability and business-fit spec". Works together with [`generation-workflow.md`](generation-workflow.md) and [`test-case-template.md`](test-case-template.md).  
> Experience source: PROJ-123 compared against a historical case set — **executable like real business work, and traceable to acceptance criteria**.

## 1. Two goals merged (neither may be dropped)

| Goal | Requirement |
| --- | --- |
| **Executable (business-facing)** | Real entry points, menu paths, wait-for-load, named test data; whoever picks up the case can click through it in the environment |
| **Traceable (acceptance-facing)** | Key rules (numeric boundaries, AND/OR, empty state) map to JIRA AC / PRD; a defect can be located to an acceptance row |

**No either/or**: a bare list of abstract rules, or "pretty operation steps" that do not trace to AC, are both unacceptable.

---

## 2. Login / account wording (mandatory)

- **Do not** hard-code specific login accounts/passwords (domain account names, personal test phone numbers, etc.)
- **Do not** leave literal `XXX` / "some permission" placeholders in the final draft — the Agent must fill in the **real permission name of the current system**

### Permission identification order

1. Permission/role notes in the current requirement document
2. Linked Confluence / design mockups
3. The team knowledge base's permission convention for that system module (the third question of Step 0.5b)
4. The minimum necessary permission inferred from the menu/feature (must be verifiable)

### Writing template

`Log in with an account that has the {system/product} [{module or operation}] permission`

**Examples (do not copy to unrelated systems):**

| Scenario | Wording |
| --- | --- |
| Module B order query | `Log in with an account that has the Module B [Order Query] permission` |
| Module B overview dashboard | `Log in with an account that has the Module B [Overview Dashboard] view permission` |
| CRM/MES/System A | Name it after the system's actual permission, e.g. "an account with CRM order-detail read-only permission" |
| Per role | `Log in with an administrator account that has the "Tag Recalculation" permission` |

**Exception**: when the requirement itself specifies an account policy/allowlist to be accepted, you may cite the account rules from the requirement, **but passwords remain forbidden**.

**Self-check failure**: if preconditions still contain `XXX` / "some permission" -> generation failed; complete it before persisting.

---

## 3. Steps must be actionable

- State the entry path clearly (e.g. `System A -> Module B -> Order Query`); the path comes from the requirement, linked docs or the KB; **do not invent menus**
- Where loading is needed, write "wait for loading to finish"
- Use stable aliases for test data (e.g. `A_ant_ok`) and give field values in preconditions
- When the text has aliases (e.g. two variant wordings of the same label), note "subject to the actual page text" in the step, and keep the verification point unambiguous

---

## 4. Module naming follows the product information architecture

- The `module` path reflects real business navigation (search, detail, dashboard, background jobs, etc.)
- Do not hang "order query verification" under an unrelated "month-end data section / dashboard sub-area"
- Follow the `/` hierarchy and the Issue Key system-prefix root node (see the module hierarchy in `generation-workflow.md`)

---

## 5. KB / history: operations go into steps, rules do not go into acceptance

- **Operation bucket must be written into steps** (path/permission/text aliases); see the two-way usage split in Step 0.5
- **Rule bucket is reference only** — never write historical/KB rules as current acceptance points
- **Self-check**: if the KB already gives an entry such as "Module B -> Order Query / Overview Dashboard" but the steps still say a generic "open the search page / view the dashboard" -> the KB was not applied; rework

---

## 6. Post-generation quality self-check (must pass)

- [ ] No hard-coded personal accounts/passwords; no `XXX` permission placeholders
- [ ] Permission wording is filled in per the **current system** (not empty boilerplate)
- [ ] Steps contain a real entry point or an explicit backend trigger
- [ ] Preconditions contain permission + test-data aliases and key field values
- [ ] Core AC (including strict boundaries) are traceable; anything uncovered is stated as uncovered
- [ ] Module path matches product navigation
- [ ] Expected results have no `[TBD]` / "pending product confirmation" placeholders; open items go to blockers, not expected_results
- [ ] Priority P1/P2/P3 is correct; no P0

The review stage checks against §5–§6 of `checklist.md` in `multica-review-test`.
