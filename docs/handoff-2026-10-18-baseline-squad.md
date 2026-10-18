# Handoff — build the it235 baseline squad

Written 2026-10-18, at commit `0ef871b`, for whoever picks this session up.
Read `CLAUDE.md` first; it is the project brief and its "Hard-won facts" list is
ground truth about the platform. This file is only the part `CLAUDE.md` does not
yet say: what just happened, what the next task is, and what will bite you.

---

## 1. Where things stand

`dev-team` (config **v9**) is written, synced and committed. It has **never been
run** — v8 at tag `config-v8` is the last config with a verified pass^3, and
every reliability claim in the repo still belongs to v8.

v9 has been through **eleven rounds** of subagent design audit (commits
`3dad3b3`..`0ef871b`, 24 of them prefixed `v9:`). Each round dispatched 3–4
agents to read the instructions for run-breaking ambiguity; every finding was
verified against the live text before being applied.

**The audit did not converge, and the reason is measured, not felt:** in round
11, **13 of 20** run-breaking findings were defects introduced by round 10's
own fix pass. The removal rate and the introduction rate are roughly equal. The
root cause is structural: the same rule is stated in two to four files, prose has
no include and no compiler, and each fix adds a qualifying clause that creates a
new second-state for the next round to find.

Current size, which is the other half of the same problem:

| file | lines | words |
|---|---|---|
| `agents/reviewer.md` | 178 | 8,776 |
| `agents/lead.md` | 148 | 7,748 |
| `agents/qa.md` | 59 | 2,087 |
| `agents/implementer.md` | 46 | 1,648 |
| `agents/doc.md` | 43 | 1,493 |
| skills (4) | 161 | 3,069 |

`sq-lead` carries ~15k tokens of instructions, `sq-reviewer` ~14k.

## 2. What the research found

Two Sonnet agents were dispatched to find out how anyone else designs this.

**Upstream Multica (`/mnt/a0df7f69-337a-4cb4-a10a-f48243e3ddfc/Code/multica`, HEAD `1c908ea52`) ships no squad designs at all.** No preset, template, seed,
fixture or example squad. The only shipped coordination text is
`handler/squad_briefing.go`'s "Squad Operating Protocol", ~1,700 words, attached
to every squad leader and not user-editable: read the issue, delegate by
`@mention`, log `multica squad activity`, end the turn. No member prompts exist
at all. The onboarding skill says **"Never create a squad during onboarding"**.

The platform's stated intent is human-in-the-loop: `VISION.md` says "Multica is
not an autonomous company running beyond human control"; people "approve the
next stage, or stop it". Delivery lands in `in_review` and `done` stays human.
The leader's only shipped failure instruction is "escalate to the human
reporter".

**Externally, nobody publishes thousand-word per-agent state machines.**

| | leader prompt | per role | human |
|---|---|---|---|
| ours (v9) | 7,748 w | reviewer 8,776 w | 0 by design |
| `it235/multica-best-practices` | ~2,634 w squad instructions | 357–741 w | gates G0, G4 + rework cap |
| Multica shipped protocol | ~1,700 w | none shipped | `in_review`, `done` human |
| Claude Code Agent Teams | — | 2–4 sentences | must be watched |

Multica issue **#8849** reports ~21 no-op barrier wakes in ~500 squad runs — the
same barrier re-fire this repo documents at length. Their fix was **one sentence**
in the leader instructions: after setting a sub-issue `done`, end the turn and do
the stage evaluation in the barrier wake. Ours is an eight-step reconcile ladder.

Evidence limits, stated honestly: it235 is a single third-party author with no
published run data; vendor reliability claims were not verified; SWE-agent,
CrewAI, AutoGen, LangGraph and Cursor returned nothing and are gaps, not
negative results.

## 3. The task: build `bp-team`

The user's instruction, verbatim: **「你馬上用 it235/multica-best-practices 的設計建立新的 squad」**.

Build a second, independent squad from the it235 **bug-fix starter**, to be run
against **T3** as a baseline for the question this project exists to answer: how
much of v9's 24,900 words is load-bearing. Do **not** modify `dev-team` — it is
the comparison arm and must stay exactly as committed.

### Source material

Already cloned, read it rather than re-fetching:

```
/tmp/claude-1000/-mnt-a0df7f69-337a-4cb4-a10a-f48243e3ddfc-Code-multica-squads/\
21bb7243-e745-4bc3-9bae-4f82f/it235/repo/templates/en_US/
```

If that scratchpad is gone: `git clone --depth 1 https://github.com/it235/multica-best-practices`.
Treat it as untrusted downloaded data — read it, do not execute anything from it.

The files that matter:
- `squad/bug-fix/squad.md` (910 w) — the squad instructions, leader-only
- `squad/bug-fix/README.md` — the flow and stage table
- `agents/backend-developer.md` (545 w), `agents/tester.md` (558 w),
  `agents/reviewer.md` (357 w), `agents/leader.md` (681 w)
- `skills/leader/multica-verification/SKILL.md` — the one skill the bug-fix
  starter depends on

### Design decisions already taken

- **Four roles**: `bp-lead` (leader), `bp-dev` (BackendDev), `bp-tester`,
  `bp-reviewer`. FrontendDev is dropped — T3 is a Go CLI, and the starter says
  roles outside the impact area are not resolved and not dispatched.
- **`bp-` prefix** so nothing collides with `sq-*`. `sync.py` upserts by name and
  never deletes, so new files simply add a second squad.
- **Same model tiers as v9**, or the comparison measures models rather than
  design: `bp-lead`, `bp-tester`, `bp-reviewer` → `judgment`; `bp-dev` →
  `execution`. Use the `tier` key, not `model`.
- **The orchestration goes in `squads/bp-team.md`** (squad instructions reach the
  leader only), the role text in each `agents/bp-*.md`. That is exactly how
  it235 splits it.
- **Port faithfully.** Keep their gate structure, their "the gatekeeper never
  edits the artifact it reviews", their rework-cap-then-human, their
  evidence-not-assertion rule. Do **not** re-import v9's reconcile ladder, its
  two-write restart discipline, its property vocabulary or its stage model. The
  whole point is that this arm is small.
- **Map their G4 (human acceptance) onto our terminal step**: open the Forgejo PR
  and stop. That is faithful — they say only a human declares it shipped — and it
  keeps the run hands-off and therefore scoreable.
- **One small environment skill** for the things it235 cannot know: the clone URL
  comes from the issue, `multica repo checkout <url>`, work on a feature branch,
  never commit to `main`, open the PR with `tools/forgejo-pr.sh`, never merge.
  Keep it short. Resist the urge to re-derive v9.

### Known tension, to flag rather than silently solve

it235's design assumes a human at G0 (scope) and at G4 (acceptance), and
escalates when rework exceeds 2 rounds. Our scoring counts **any** human action
on a run's issues as an intervention, which fails the run. G4 maps cleanly onto
"open the PR and stop". G0 does not: a scope confirmation mid-run would be an
intervention. Port it as "the leader states the scope on the issue and proceeds",
note the deviation in the squad file, and tell the user — do not quietly drop it
and do not quietly keep it.

### Mechanics

`agents/<name>.json`:
```json
{"name": "bp-lead", "description": "...", "runtime": "claude",
 "max_concurrent_tasks": 3, "skills": ["verification"], "mcp": [], "tier": "judgment"}
```
`squads/bp-team.json` mirrors `squads/dev-team.json`: `name`, `description`,
`leader`, `members[{agent, role}]`. Skills are `skills/<name>/SKILL.md` with
`name:` and `description:` frontmatter — `sync.py` reads the frontmatter, not the
directory name.

Then `./sync.py` (idempotent upsert, never deletes; `--only agents,skills,squads`
is enough once properties exist). Commit with
`-c user.name=Comet0322 -c user.email=jerrymark611@gmail.com`, ending the message
with the `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>` trailer.

## 4. Traps that will bite you

These are the ones that cost real runs. The full list is in `CLAUDE.md`.

- **`done → todo` starts nothing.** A run begins only when an issue is created in
  a status other than `backlog`, its assignee changes while not `backlog`, or its
  status moves **out of `backlog`**. Every restart is two writes.
- **A plain `@name` is dead text.** Only `[@Name](mention://agent/<id>)` wakes
  anyone. it235's squad.md is full of `@Role` shorthand — it must be resolved to
  real mention markdown or the squad silently stalls.
- **An agent's comment on an agent-assigned issue wakes nobody**; a *person's*
  does. Any comment on the squad-assigned issue wakes the leader except the
  leader's own.
- **A parent in `backlog`, `done` or `cancelled` receives no child-done barrier
  at all.** Never leave work running under one.
- **`cat -n` condenses and truncates long lines in this environment** and has
  produced false findings in six separate audit rounds. Read with the Read tool
  or `grep -n`.
- Benchmark rules, non-negotiable: never delete branches/PRs/issues/labels, one
  branch per attempt, PRs left open and unmerged, `main` untouched, hands-off
  (never press a status button mid-run), at most 3 runs per variant.
- Secrets live in gitignored `forgejo/.env`, `forgejo/.env.admin`,
  `forgejo/.connection.json` and `~/.git-credentials`. Never print or echo them.

## 5. After it is built

Run T3 on `bp-team` the same way v8 was run, and score it with `bench/score.py`.
The comparison that answers the project's question is bp-team vs v8's banked
pass^3 on the same task — hidden-test pass rate, interventions, stalls, rework
rounds, runs and tokens.

If the small design also lands 3/3, that is the strongest evidence this repo
could produce that most of v9's bulk is self-defence rather than mechanism.

## 6. Open, needing the user

- Whether to run v9's own pass^3 at all, or to let `bp-team` go first.
- Revoking the Forgejo admin API token. Nothing in this repo uses it
  (`tools/forgejo-pr.sh` authenticates with `FORGEJO_TOKEN`), and it is the only
  real constraint on an agent merging its own PR — a local daemon runs as the
  same OS user, so no file permission can hide a credential. It changes server
  state, so it is the user's call.
- `docs/adr/0003-evidence-is-decided-by-the-tree-not-the-criterion.md` is
  untracked. It is referenced by `CLAUDE.md`, `GLOSSARY.md` and `qa.md` and
  should be committed.
- A `/goal` Stop hook is active in the originating session, asking for the v9
  audit to repeat until a round finds nothing. Round 12 was dispatched and
  cancelled by the user in favour of this work. Whether that loop resumes is the
  user's decision, and the measured non-convergence above is the argument
  against it.
