---
name: repo-intake
description: Mechanical survey of a repository before writing a spec against it; produces the Repo intake section with pasted evidence
---

# Repo intake

Run this on **every** repository before you write a spec against it, including one the squad
has worked on before: its state may have changed since. It is a fixed set of commands whose
real output goes into the spec's `Repo intake` section. You may not assert any of it from
reading the code — the rule is the same one that applies to a bug's Reproduction: run it,
paste what you got.

Check out the repo first (`multica repo checkout <url>`) and work on `origin/main`.

## The checks

| # | Check | Command (Go; adapt per language) | Why it matters |
|---|---|---|---|
| 1 | The build works on `main` | `go build ./...` | A broken baseline makes every later verdict meaningless |
| 2 | **The test suite exists AND passes on `main`** | `go test ./...` | This is the baseline review and QA protect |
| 3 | Formatter and vet state on `main` | `gofmt -l .` and `go vet ./...` | Tells you whether "clean" is reachable or whether the baseline is already dirty |
| 4 | A conventions file | `ls AGENTS.md CLAUDE.md CONVENTIONS.md CONTRIBUTING.md` | If one exists it is the conventions source and you cite it; if not you must write the conventions yourself |
| 5 | What `.gitignore` covers | `cat .gitignore` | A repo that does not ignore its build output will get the build output committed |
| 6 | Dependencies | `cat go.mod`, `ls vendor 2>/dev/null` | Whether the squad may add a dependency, and whether tests need the network |
| 7 | **The squad can push** | `git push --dry-run origin HEAD:refs/heads/intake-probe-<date>` | Otherwise this is discovered after all the work is done |
| 8 | **The branch this run will use is free** | `git ls-remote --heads origin <branch>` | A branch left by an earlier attempt is adopted silently by the first stage (`handoff-protocol` checks out an existing remote branch on purpose, so later stages find the earlier ones' work). Every commit on it then falls inside the first ticket's range, and the verifier briefs stage 1 to undo commits it never made and may not touch. Empty output is the pass; anything else means choose another branch name |

## What each outcome means

- **The repository is empty** (a README and nothing else) → 1 and 2 fail and that is **fine**: there is no baseline to protect because there is nothing there yet, and the first ticket establishes the build and the test command. Record it as a greenfield intake, say so in the spec's `Repo intake`, and go on. This exception is for an empty repository only — code with no tests is still outside the boundary.
- **1 or 2 fails on a repository that has code** → the repository is **outside the capability boundary**, for the same
  reason a repo with no tests is: review and QA would have no baseline, and the squad could
  not tell its own regressions from the ones already there. Say so in chat and stop. The
  nearest thing is **not** a spec to green the baseline — that is work in the same
  repository, so it is outside the boundary for the same reason. Say that a person has to
  green it first, and that the squad can take the work once they have.
- **3 is already dirty** → record the exact baseline (which files `gofmt -l` prints, which
  vet warnings exist). The standard for the branch becomes "no NEW violations", not "clean".
  Never ask an implementer to tidy files the spec does not touch.
- **4 found a file** → read it and cite it as the conventions source in the Impact analysis;
  do not restate it. **4 found nothing** → you must derive the conventions by observation
  (error-message shape, test layout and naming, logging, what the existing code does and
  does not import) and write them into the Impact analysis yourself, and say in chat that
  you did so because the repo documents none.
- **5 or 6 reveals a gap** → put it in the Conventions list (for example "the build output
  is not ignored, so never commit the binary").
- **7 fails** → stop. The repository is not set up for this squad; say exactly what access
  is missing and who must grant it. This is a human's setup task, not work the squad can do.

## Output

A `Repo intake` section in the spec: one row per check with the command, its exit status and
its real output (trimmed to the relevant lines), then one line naming the conventions source
(a file, or "derived by observation — the repo documents none"). Never paraphrase, and never
write "tests pass" without the output that shows it.
