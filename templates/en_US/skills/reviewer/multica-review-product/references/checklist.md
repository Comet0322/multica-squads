# PRD Review Checklist

Use together with [`review-workflow.md`](review-workflow.md). **Must Fix** causes FAIL; **Suggest** / **Nit** never cause FAIL on their own.

## 0. Materials

- [ ] PRD link or full text (from the Leader's dispatch)
- [ ] Issue / Story Key / business background
- [ ] Optional: prototype, data definitions, dependent systems
- [ ] Read the **full text** (not just a summary)
- [ ] PRD missing or inaccessible -> **BLOCKED**

## 1. Value judgment

- [ ] The problem is real and urgent (not "doing it for the sake of doing it")
- [ ] Expected benefit / KPI- / G- is measurable
- [ ] Scope matches effort; if too large, suggest phasing (Suggest or Must Fix depending on severity)
- [ ] Lower-cost alternatives were considered (configuration, operations, reuse)
- [ ] No KPI / success criteria -> usually **Must Fix**

## 2. Logical closure

- [ ] The goal -> solution -> acceptance (AC-) chain is complete and consistent
- [ ] User roles and permissions cover all scenarios; no privilege-escalation or missing-permission paths
- [ ] Main flow + exception flows + boundary conditions
- [ ] Empty, error and no-permission states are defined
- [ ] **BR-** has no contradictions; state machine is closed
- [ ] Field/metric definitions: numerator and denominator, data source, refresh frequency (when involved)
- [ ] Dependencies and assumptions are listed explicitly
- [ ] **Scope and non-scope** are clear; no implicit scope creep
- [ ] Cross-system / API / write-back: owners and boundaries are clear

## 3. Clarity (Q- numbering)

- [ ] No vague words: "appropriate", "optimize", "etc.", "and so on", "as the case may be", "good experience"
- [ ] Every key capability in an FR- has a testable **AC-**
- [ ] Fields, states and permission rules are defined (not "TBD" scattered through the text)
- [ ] When prototype/diagram and text conflict, the PRD states which prevails
- [ ] **OP-** is maintained in one place; items blocking development are marked; each has an Owner or a clear "pending whom"
- [ ] Issues numbered Q-001... (type: value / logic / clarity)

## 4. Numbering and structure (Squad convention)

- [ ] G- / FR- / BR- / AC- / KPI- / OP- / RISK- used consistently
- [ ] AC- can be verified objectively (no purely subjective wording)
- [ ] Unconfirmed items are not mixed into confirmed FR-/AC-

## 5. Knowledge base (optional)

- [ ] If the KB is queried: only check whether terms / entry points / permission aliases are written into the PRD
- [ ] Did **not** write the KB's historical rules up as defects of the current PRD
- [ ] KB unavailability was noted and did not block the review

## 6. Pre-output self-check

- [ ] Must Fix / Suggest / Nit are distinguished
- [ ] Every Must Fix includes a PRD location (section or number)
- [ ] Value / logic summary written
- [ ] Even on PASS, wrote the key points checked and residual OP- / risks
- [ ] Verdict reported only to the Leader (no @PM, no pushing development)
