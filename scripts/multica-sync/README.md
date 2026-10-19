# Multica template sync

Optional automation that pushes this repo's **skills / agents / squad** templates (`templates/en_US`) to your Multica workspace.
Python 3.9+, **stdlib only**, fully **idempotent**.

> Prefer copy-paste? Use [`templates/en_US/squad/software-development`](../../templates/en_US/squad/software-development) directly — the starters work on their own, no scripts needed.

## One-shot bootstrap (recommended entry)

`bootstrap_squad.py` runs 5 steps in dependency order, joining on **names** (update if it exists, create only if missing),
so no UUID ever needs to be committed to the repo:

1. **skills** — `templates/en_US/skills/**/SKILL.md` → `POST /api/skills` / `PUT /api/skills/{id}`
2. **agents** — `templates/en_US/agents/<stem>.md` → `POST /api/agents` (needs `runtime_id`, auto-detected) / `PUT /api/agents/{id}`
3. **squad** — `POST /api/squads` (`leader_id` required) + `PUT` to write the squad instructions
4. **members** — `POST /api/squads/{id}/members` (`member_type=agent` + `role`)
5. **bindings** — `POST /api/agents/{id}/skills/add` (ensure, append) or `PUT /api/agents/{id}/skills` (replace, exact overwrite)

The fastest path is two commands — without `--config` the bundled `squad-bootstrap.example.json` is used (15 roles with their skills):

```powershell
cd scripts/multica-sync

$env:MULTICA_API_TOKEN = "mul_xxx"                           # recommended; cookie auth below
$env:MULTICA_API_URL   = "https://your-multica.example.com"  # or put it in config.local.json

python bootstrap_squad.py --workspace 100 --dry-run   # preview first
python bootstrap_squad.py --workspace 100             # then execute
```

To customise roles or mounts, copy the config first:

```powershell
cp squad-bootstrap.example.json squad-bootstrap.json
python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json
```

Common variants:

```powershell
python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json --sync-skills all
python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json --bind-mode replace
python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json --only tester
python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json --write-mapping agent-mapping.json
```

| Common flag | Description |
| --- | --- |
| `--workspace` | workspace slug or UUID (or `MULTICA_WORKSPACE`) |
| `--config` | bootstrap config, default `squad-bootstrap.json` |
| `--sync-skills` | `needed` (default, only skills the config references) / `all` (every template skill) / `none` |
| `--bind-mode` | `ensure` (default, append missing bindings) / `replace` (overwrite exactly with the list) |
| `--runtime` | runtime_id used to create agents; auto-detected when omitted |
| `--dry-run` | print the planned actions without writing |

> Creating an agent requires a runtime: by default the script takes the first available runtime from `GET /api/runtimes?owner=me`;
> if no runtime is visible in the workspace, pass `--runtime <runtime-id>` explicitly.

## Authentication

**Option A — API token (recommended)**

```powershell
$env:MULTICA_API_TOKEN = "mul_xxx"
```

**Option B — browser cookie** (DevTools → copy from the Headers of any Multica request)

```powershell
$env:MULTICA_COOKIE = "multica_auth=...; multica_logged_in=1; ..."
$env:MULTICA_CSRF   = "<value of x-csrf-token or the multica_csrf cookie>"
```

**Base URL** — the scripts **embed no address**; resolution order: `--url` > `MULTICA_API_URL` > `config.local.json`

```powershell
$env:MULTICA_API_URL = "https://multica.example.com"
# or in config.local.json: { "base_url": "https://multica.example.com", "workspace": "100" }
```

Warning: never commit tokens / cookies / internal addresses to Git. `config.local.json`, `squad-bootstrap.json` and `agent-mapping.json` are already in `.gitignore`.

## Clone a squad across workspaces

You already have a squad in one workspace and want an exact copy in another (agents / skills are created if missing, reused and bound if present):

```powershell
cd scripts/multica-sync

# preview
python clone_squad.py `
  --from-workspace 100 `
  --from-squad <source-squad-uuid> `
  --to-workspace 200 `
  --dry-run

# execute
python clone_squad.py `
  --from-workspace 100 `
  --from-squad <source-squad-uuid> `
  --to-workspace 200

# when the target workspace has no runtime
python clone_squad.py ... --to-workspace 200 --runtime <runtime-id>

# force-overwrite existing same-name skill / agent / squad content in the target
python clone_squad.py ... --update-skills --update-agents --update-squad
```

| Flag | Description |
| --- | --- |
| `--from-workspace` / `--from-squad` | source workspace slug/UUID + source squad UUID (`/squads/<uuid>` in the squad page URL) |
| `--to-workspace` | target workspace slug/UUID |
| `--to-squad-name` | target squad name (defaults to the source name) |
| `--runtime` | runtime_id for newly created target agents; auto-detected by default |
| `--update-skills` / `--update-agents` / `--update-squad` | overwrite content when a same-name item already exists (default: reuse without overwriting) |

> Cloning joins on **names** (same as bootstrap), so re-runs are idempotent; use `--dry-run` to preview.
> The base URL comes from `--url` / `MULTICA_API_URL` / `config.local.json`; the scripts embed no address.

## Scripts

| Script | Purpose |
| --- | --- |
| `bootstrap_squad.py` | **One-shot squad build**: skills → agents → squad → members → bindings (idempotent, joined on names) |
| `clone_squad.py` | **Clone a squad across workspaces**: pulls agents/skills/bindings from the source API, creates/reuses/binds them in the target workspace (idempotent, joined on names) |
| `sync_skills.py` | `templates/en_US/skills/**/SKILL.md` → create / overwrite in the workspace |
| `sync_agents.py` | `templates/en_US/agents/*.md` → `PUT /api/agents/{id}`; `--squad` auto-maps by role |
| `list_squad_skills.py` | List a squad's agents and their bound skills |
| `squad_mapping.py` | role → template stem mapping (used by `sync_agents.py`) |
| `multica_client.py` | Minimal REST client (stdlib only) |
| `repo_paths.py` | Template path resolution (`templates/en_US` first, flat layout supported) |

## Paths

Reads `templates/en_US` by default; override with:

```powershell
$env:MULTICA_TEMPLATE_LANG = "en_US"            # reads templates/en_US
$env:MULTICA_TEMPLATES_DIR = "templates/en_US"  # or point at a directory explicitly
```

`instructions_file` in the config accepts three forms: an absolute path, `templates/...`, or a path relative to the templates root
(e.g. `squad/software-development/squad.md`).

## Checking a software-development-gateway run

`check_sdg_run.py` checks one finished Issue of the `software-development-gateway` squad against its 14 acceptance criteria (handoff never stalls, members post their own comments, verbatim delivery templates, one artifact per review, review rounds, step order, every push through the git gateway by the owning role, spec-branch contents, one MR whose tests pass when re-run, final Gate, document headings). It prints `PASS` / `FAIL` / `SKIP` per criterion and exits non-zero on any `FAIL`.

```bash
cd scripts/multica-sync
export MULTICA_API_TOKEN=mul_xxx MULTICA_API_URL=https://your-multica.example.com
python check_sdg_run.py <ISSUE-KEY> --workspace <workspace-slug> --ui yes \
  --repo-url <clone URL of the product repo> \
  --backend-container <multica backend container> --gateway-container <git gateway container>
```

`--ui no` for a task without a user interface (UI and FRONTEND must then be skipped). Without `--backend-container` / `--gateway-container` the criteria that read those logs print `SKIP`. `--path-prefix` puts a directory (for example a venv's `bin` with pytest) first on `PATH` when the script re-runs the Test command.
