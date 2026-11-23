# Vendored skills (used unchanged)

Copied verbatim by `tools/vendor-skills.sh`; never edit them here. Both sources are MIT. The two squads use **disjoint** method sets, so a difference between them is attributable to the method, not to a mixture.

| Squad | Source | Pin | Attached skills |
|---|---|---|---|
| `dev-mp` | mattpocock/skills | 1.3.1 (Claude plugin cache) | lead: grilling, domain-modeling, to-spec, to-tickets, pr, retro. builder: tdd, diagnosing-bugs, codebase-design. verifier: code-review |
| `dev-ps` | michael-denyer/pstack-claude (port of Lauren Tan's pstack) | 66181d3 | `ps-lead`: poteto-mode and the skills it routes to (see `agents/ps-lead.json`); the whole pstack skill set is vendored, only these are attached |

Deviations, all forced:
- pstack's `tdd` is **not** vendored: the name clashes with mattpocock's `tdd` and a workspace has one namespace. poteto-mode's Bug fix playbook mentions it; `ps-lead` has no `tdd` skill.
- pstack's `pstack:poteto-agent` plugin subagent is not installed in Multica; `ps-lead.md` says to use the general-purpose subagent with poteto-mode's `worker.md` kickoff. No `/setup-pstack` runs, so poteto-mode's default models apply.
- mattpocock's skills ask for `/setup-matt-pocock-skills`; `agents/mp-lead.md` supplies the issue-tracker mapping instead.

Everything else ours lives in `agents/mp-*.md`, `agents/ps-lead.md` and `skills/flat-protocol` (platform mechanics only; the name predates the split).
