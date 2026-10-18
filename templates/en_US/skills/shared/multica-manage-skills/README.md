# multica-manage-skills usage guide

Manage Skills through the Multica API (create / update / publish / delete). All API addresses are placeholders; fill in your own Multica address and token via environment variables.

## 1. Configure environment variables

```bash
export MULTICA_API_URL="https://your-multica.example.com"   # placeholder address
export MULTICA_API_TOKEN="mul_xxxxxxxxxxxxxxxx"             # your API token
```

`scripts/multica_api.py` reads `MULTICA_API_URL` first and errors out with a prompt to set it if missing.

## 2. Install dependencies

```bash
cd scripts
pip install requests   # the only dependency
```

## 3. Main usage

```bash
# list all skills
python scripts/multica_api.py list

# upload / update a skill directory
python scripts/multica_api.py push --path /path/to/your-skill

# delete
python scripts/multica_api.py delete --name your-skill-name
```

See `references/api_reference.md` for API fields and response structure.

## 4. Notes

- `MULTICA_API_TOKEN` is a sensitive credential: **do not commit it**; keep it in the shell environment or a secrets manager.
- `MULTICA_API_URL` must not contain a real production address in the repo.
