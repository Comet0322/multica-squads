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

## What each outcome means

- **1 or 2 fails** → the repository is **outside the capability boundary**, for the same
  reason a repo with no tests is: review and QA would have no baseline, and the squad could
  not tell its own regressions from the ones already there. Say so in chat and stop. Offer
  the nearest thing instead: a spec whose single goal is to make the baseline green, agreed
  as its own piece of work first.
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
