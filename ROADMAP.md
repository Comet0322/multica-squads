# Roadmap

## v0.1 (Current)

```text
Software Development Starter
├── 7 roles (Leader / Architect / Designer / FrontendDev / BackendDev / Tester / Reviewer)
├── 1 Squad (conditional routing: any role may be absent)
├── 6 Skills
├── 1 Issue template (with an "affected ends" scope declaration)
└── 1 Workflow
```

## Not yet exercised on real tasks

Proven end to end on a Forgejo test repo (backend, frontend, fullstack, epic with stage-ordered slices, two Issues editing the same response, a spec contradiction escalated to a human, a UI-design Issue through the Designer, a bug fix by the bug-fix squad). Still to prove:

- A professional review that fails three rounds in a row and escalates to a human.
- DevOps and G2.5 (needs a real CI/CD platform behind `multica-platform-jenkins`).
- The Figma, Jenkins, Apifox, Confluence, JIRA and knowledge-base platform shells against real systems.
- Automatic notification when a human merges a PR (today a human comment wakes the Leader).
- Two slices of the same epic stage that touch the same files.

## software-development-gateway (experimental)

Proven on a local GitLab test repo (greenfield CLI, backend + frontend, three Issues in parallel, Issues filed from a PM chat). Still to prove, per [`pilot-test-plan.md`](templates/en_US/squad/software-development-gateway/pilot-test-plan.md):

- A company repo with existing code, and the runtime in a Kubernetes pod with the gateway sidecar.
- A chat spec sent back for wording, a review failing three rounds, a `**Blocked**` stop.
- A git host other than GitLab in the gateway.
- Repo alias, branch prefix and default branch read from one config instead of `squad.md` and the PM prompt.

## Internal-edition back-migration

> This repo shares a common origin with an internal fork (CORP). Batched plan for back-porting validated capabilities from the internal fork to the public edition.

| Batch | Content |
| --- | --- |
| **B1** | 5 methodology docs (`FLOW` / `role-skills-architecture` / `test-automation-in-repo` / `multi-repo-and-issue-links` / `platform-collaboration`) + `templates/MULTICA.md` |
| **B2** | 9 new skills: `multica-backend-impl`, `multica-frontend-impl`, `multica-test-orchestration`, `multica-test-t1-design`, `multica-test-t2-coverage`, `multica-test-t3-ui-automation`, `multica-test-t3-api-automation`, `multica-platform-apifox`, `multica-platform-figma` |
| **B3** | Upgrade existing skills (6 `multica-review-*`, `multica-technical-design`, `multica-pm-requirement-spec`, 3 `multica-artifact-*-sync`, script enhancements for `multica-platform-jira` / `-confluence`, `multica-manage-skills`) |
| **B4** | agents / squad sync; remove the superseded `multica-test-design` / `multica-test-automation` / `multica-artifact-test-sync`; wrap up README / AGENTS / CHANGELOG |

### Migration red lines

- No internal hosts / IPs / account-system env vars — placeholders only
- Do not migrate implementations coupled to company-internal systems (BOSS / AngelAlign in `multica-design-ui-impl`, the 138 Bridge in `multica-platform-knowledge-base`, SynapseRT in `import_to_jira.py`)
- Keep existing public skill names; upgrade content in place, no renames

## Near term

- [x] Starter-first structure with `templates/` as the only entry
- [x] Bug Fix Starter (minimal combo that skips Architect)
- [x] Frontend/backend split + conditional routing (any role may be absent; the Issue declares the affected ends)
- [x] Template and docs trees under `en_US/`; the repository is English-only
- [ ] Validate the orchestration on real requirements: four squad variants (full flow / no design / no frontend / no backend)
- [ ] Technical Research Starter (Researcher → Leader gate (multica-verification skill) → Human)
- [ ] More stack-specific verification command tables (Java, Rust, monorepo)
- [ ] Real pilot retro example with sample data

## Later

- [ ] More real cases and community feedback
- [ ] Model-fit guide (division of labor between weaker models and strong reasoning models)
- [ ] Optional Multica Skill pack published to the Skill Registry

## When is it Stable

Not "templates are written," but enough real Issues run across different projects, agents, and models.

## Relationship to related projects

- Complements **oh-my-multica** (deterministic delivery Loop / DAG)
- Complements **multica-agent-workflow-template** (agent count & skill routing design)
- This repo focuses on Squad Instructions, gate conventions, Starter templates, and team rollout

## Non-goals

- No orchestration engine inside this repo
- No single CLI or model-vendor lock-in
