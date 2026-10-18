# multica-test-t1-design / scripts

> T1 landing scripts for this skill; content conventions live in `../references/`. Collection goes through the platform skills (`fetch_all` locates platform scripts by **skill name**).

## Scripts shipped with this skill

| Script | Purpose |
| --- | --- |
| `fetch_all.py` | One-shot collection of Issue + team docs (including images) + design files (calls `multica-platform-jira` / `-confluence` / `-figma`) |
| `generate_xmind.py` | Functional cases -> dual-format XMind (Zen JSON + XMind 8 XML) |
| `dedup_check.py` | Test-case dedup check |
| `generate_test_cases.py` | Structured test-case dataclass helper |
| `local_env.py` | Load `config.local.env` / environment variables |

## Team-provided (**not shipped with this skill**)

The script that bulk-imports cases into the test-management platform is tightly bound to a specific tool (Jira case plugin / TestRail / Zephyr / in-house platform...) and cannot be generalized.

- Conventional name: `import_to_tracker.py`
- Interface and acceptance conventions: see [`../references/import-contract.md`](../references/import-contract.md)
- **Hard constraint**: run only after an explicit human go-ahead; import only once per batch

## Platform single-step debugging (not the daily T1 entry point)

| Platform skill | Script |
| --- | --- |
| `multica-platform-jira` | `get_issue.py` / `jira_cli.py get-issue` |
| `multica-platform-confluence` | `fetch_page_by_url.py` |
| `multica-platform-figma` | `fetch_file.py` |

## Common commands

```bash
# Collect
python scripts/fetch_all.py --jira-url https://your-domain.atlassian.net/browse/PROJ-123 -o ./data

# XMind (dual format)
python scripts/generate_xmind.py \
  --input ./data/test_cases.json \
  --output ./data/test_cases_PROJ-123.xmind \
  --project PROJ

# Import (team-provided script; functional cases only; after the go-ahead)
python scripts/import_to_tracker.py \
  --jira-url "https://your-domain.atlassian.net/browse/PROJ-123" \
  --input ./data/test_cases.json \
  --suite-name "<requirement title>"
```

## Encoding and case-tree notes

- **UTF-8**: JSON / XMind / script stdout are all UTF-8; if the Windows terminal is garbled, run `chcp 65001` first or set `PYTHONIOENCODING=utf-8`
- **Case tree**: both XMind and the import script rely on the `/` hierarchy in the `module` field; a wrong hierarchy hangs cases on the wrong node
- **Dedup**: generation dedups by "module + scenario + operation path"; the import stage does another dedup on the target platform; do both
