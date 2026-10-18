# multica-platform-confluence Usage Guide

Confluence platform shell: publish design documents / PRDs to pages in a given space. All URLs and credentials are placeholders; fill in your own Confluence address in `.env`.

## 1. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in:
#   CONFLUENCE_URL=http://your-confluence.example.com:8090
#   CONFLUENCE_USER=<your-user>
#   CONFLUENCE_PASS=<your-pass>
#   CONFLUENCE_AUTH_MODE=basic
#   ATLASSIAN_USER=<your-domain-user>      # optional, domain account takes precedence
#   ATLASSIAN_PASS=<your-domain-pass>
```

The space list lives in `spaces.json` (sanitized into a placeholder skeleton); fill in `key` / `name` for your Confluence instance.

## 2. Install dependencies

```bash
cd scripts
pip install -r requirements.txt
```

## 3. Main scripts

| Script | Purpose | Example |
|---|---|---|
| `publish_design.py` | Publish a Markdown design document as a Confluence page | `python scripts/publish_design.py <ISSUE_KEY>` |
| `fetch_page.py` | Fetch a page and convert it to Markdown (for further editing) | `python scripts/fetch_page.py <CONFLUENCE_PAGE_ID> -o out.md` |
| `confluence.sh` | Bash wrapper (create / update / attachments) | `bash scripts/confluence.sh --help` |

Page templates are in `scripts/templates/` (`design-template.md` / `prd-template.md`).

## 4. Validate

```bash
bash scripts/validate.sh   # check credentials / space config
```

## 5. Notes

- `<CONFLUENCE_PARENT_PAGE_ID>` and the space `key` in `config.yaml` are placeholders; fill them in for your instance.
- Do not commit real page IDs / space keys / tokens.
