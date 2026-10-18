# multica-platform-jira Usage Guide

JIRA platform shell: read/write issues, comments, status transitions, DingTalk notifications. All URLs and credentials are placeholders; fill in your own JIRA address in `.env`.

## 1. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in:
#   JIRA_URL=http://your-jira.example.com:8080
#   JIRA_USER=<your-user>
#   JIRA_PASS=<your-pass>
#   ATLASSIAN_USER=<your-domain-user>      # optional, domain account takes precedence
#   ATLASSIAN_PASS=<your-domain-pass>
#   DINGTALK_WEBHOOK=<webhook-token>       # optional, for notifications
```

Credential lookup priority: `ATLASSIAN_USER/PASS` -> `JIRA_USER/PASS` -> `.env`.

## 2. Main entry point

The main script is `scripts/jira.sh` (bash), which supports subcommands. Common ones:

```bash
bash scripts/jira.sh --help
bash scripts/jira.sh issue <ISSUE_KEY>              # show issue details
bash scripts/jira.sh comment <ISSUE_KEY> "Conclusion..."  # add a comment
bash scripts/jira.sh transition <ISSUE_KEY> "Approved"  # transition status
bash scripts/jira.sh list --project <PROJECT_KEY> --status "Pending Review"  # list by condition
```

Field IDs (such as `<JIRA_CUSTOM_FIELD_XXX>`) are given as placeholders in `config.yaml`; replace them with the real customId values of your JIRA instance.

## 3. Validate

```bash
bash scripts/validate.sh   # check credentials / required fields
```

## 4. Notes

- The `customId`, `pageId` and project `id` values in `config.yaml` are placeholders; **fill them in for your JIRA instance**.
- Do not commit real tokens / passwords in `.env` or `config.yaml`.
