# software-development-gateway

Issue (or a chat with the PM) -> PRD -> design -> UI -> backend + frontend -> acceptance tests -> **one merge request** for a Human. One Reviewer judges every artifact. **No agent ever holds a git credential**: every clone, push and MR goes through the MCP git gateway sidecar (`scripts/git-gateway/`), so the squad can run in a Kubernetes pod whose runtime has no token.

Status: **experimental**. Proven on a local GitLab test repo (see [When it was tested](#when-it-was-tested)); company pilot plan: [`pilot-test-plan.md`](pilot-test-plan.md).

## When to use

- Agent runtimes must not see git tokens (shared clusters, regulated environments).
- You want one Reviewer and a short, observable handoff instead of per-role reviewers.
- No CI/CD is required: the Reviewer re-runs the tests itself.

## Roles

| Agent (stem) | Produces | Skills |
| --- | --- | --- |
| SdgLeader (`sdg-leader`) | dispatches, checks each delivery against its template, opens the MR | none (gateway MCP for `open_mr` only) |
| SdgPM (`sdg-pm`) | PRD `docs/prd/<KEY>.md`; in a chat, the issue itself | `sdg-member-rules`, `sdg-review-prd` |
| SdgArchitect (`sdg-architect`) | design `docs/design/<KEY>/design.md` | `sdg-member-rules`, `sdg-review-design` |
| SdgDesigner (`sdg-designer`) | UI spec `docs/design/<KEY>/ui.md` (only when the design says there is a UI) | `sdg-member-rules`, `sdg-review-ui` |
| SdgBackend / SdgFrontend | code + unit tests on `demo/<KEY>-backend` / `-frontend` | `sdg-member-rules`, `sdg-review-code` |
| SdgTester (`sdg-tester`) | acceptance tests on `demo/<KEY>` (merges both code branches) | `sdg-member-rules`, `sdg-review-test` |
| SdgReviewer (`sdg-reviewer`) | one `REVIEW ...: PASS|FAIL` per dispatch | `sdg-member-rules` + all five `sdg-review-*` |

## Where each rule lives (exactly one place)

| Rule | Lives in | Read by |
| --- | --- | --- |
| Flow, delivery templates, send-back, round limit, Gate | [`squad.md`](squad.md) | Leader only |
| Repo access only through the gateway, how to clone/push, how to deliver, Blocked | `sdg-member-rules` | every member |
| What a document must contain (template) and how it is judged (checklist) | `sdg-review-<type>` | its producer **and** the Reviewer |
| What the role produces | the agent prompt | that agent |

## Setup

1. Run the gateway (`scripts/git-gateway/README.md`): register the repo alias, branch prefix and default branch in its config; the token stays in the sidecar.
2. In `squad.md` and the PM prompt (`templates/en_US/agents/sdg-pm.md`), replace the repo alias `orchestration-demo`, the branch prefix `demo/` and the default branch `main` with your values.
3. Do **not** configure repositories in the Multica workspace settings: Multica injects them, with `multica repo checkout` guidance, into every agent and lures agents away from the gateway.
4. `cd scripts/multica-sync && python bootstrap_squad.py --workspace <workspace-slug> --config software-development-gateway.json --bind-mode replace --runtime <runtime-id>`; read the squad, agents and skills back to confirm.

## Why it works

- **The Leader pastes a verbatim delivery template into every dispatch**, so a member never guesses the format and the Leader checks each delivery line by line before review.
- **Members post their delivery themselves** with the `multica` comment command: a comment that Multica synthesizes from a run's final answer does not wake the Leader, which is what made squads stall silently.
- **One artifact, one review skill, one review dispatch**; the Reviewer reads the artifact at its commit and re-runs its tests, so it never judges pasted text.
- **The gateway enforces what prompts cannot**: repo aliases only, a branch prefix, no default-branch or force push, and `git_push` only accepts directories made by `git_clone`.
- **A chat spec is the human's**: the PM pastes an all-PASS self-check before filing, and the squad may fix only its wording.

## Common failure modes

| Symptom | Cause | Fix |
| --- | --- | --- |
| Squad stops after a member's result | the member ended with a final answer instead of posting a comment | keep rule 4 of `sdg-member-rules`; check backend logs for `comment created` |
| PM says the repo is "not configured" or works in another checkout | workspace repositories are configured | remove them (setup step 3) |
| Leader shortens the template, member answers in Markdown | template paraphrased | keep "paste verbatim" in `squad.md`; the Leader sends malformed deliveries back |
| Push rejected "was not created by the git_clone tool" | agent worked in its current directory | expected: the gateway sends it back to `git_clone` |
| Review line says `CODE` or lists files | old REVIEW template | `REVIEW <ARTIFACT> <Branch>@<Commit>` |

## Checking a run

`scripts/multica-sync/check_sdg_run.py` checks one finished Issue against 16 acceptance criteria (see the script header and `scripts/multica-sync/README.md`).

## When it was tested

Local GitLab, greenfield repo, Claude Sonnet for every agent: a CLI tool without UI, a backend + frontend web app, three Issues in parallel, and two Issues filed from a PM chat; every criterion passed on the final version. Not yet exercised: a real company repo with existing code, a Kubernetes pod, a review failing three rounds, a chat spec sent back for wording, a `**Blocked**` stop.
