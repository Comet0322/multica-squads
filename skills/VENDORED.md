# Vendored skills (used unchanged)

Copied verbatim by `tools/vendor-skills.sh`; never edit them here. Both sources are MIT.

| Source | Pin | Skills |
|---|---|---|
| mattpocock/skills | 1.3.1 (Claude plugin cache) | tdd, diagnosing-bugs, codebase-design, code-review, to-spec, to-tickets, pr, retro, domain-modeling, grilling |
| michael-denyer/pstack-claude (port of Lauren Tan's pstack) | 66181d3 | architect, interrogate, principle-prove-it-works, principle-sequence-verifiable-units |

Not used: pstack's `poteto-mode` router and playbooks (they bring model configuration and routing hooks), pstack's `tdd` (same name as mattpocock's), mattpocock's `grill-with-docs`/`implement`/`implement-spec` (orchestrators that a human invokes; their job is `fl-lead`'s dispatch).
Our own adaptation lives only in `agents/fl-*.md` and `skills/flat-protocol`; `agents/fl-lead.md` supplies the issue-tracker mapping the skills ask `/setup-matt-pocock-skills` for.
