# Multimodal Content Handling (HTML + Images)

> Consolidated from `test-case-generator-squad`. Collection scripts go through the platform skill; the Agent's read phase must still follow these rules.

## Goal

Do not miss tables, lists, flowcharts, UI screenshots, data dictionaries, or other information in requirement documents.

## HTML / ADF

Extract from Jira ADF and Confluence Storage Format:

- **Tables**: row/column correspondence, meaning of headers
- **Lists**: order and nesting
- **Formatting**: bold/highlighted keywords
- **Code blocks / macros**: API examples, configuration

**Do not** strip tags and turn tables into scattered text.

The `fetch_all` summary JSON contains `rich_content` and `confluence_details`; stderr prompts when there are tables/images.

### `fetch_all.py` output fields (the Agent must read)

Summary file: `summary_{timestamp}.json`

| Field | Description |
| --- | --- |
| `jira.key` / `jira.summary` | Issue Key and title |
| `jira.description_text` / `description_html` | Jira description (text + HTML) |
| `jira.image_attachments[]` | Jira image attachments (from platform `get_issue.py`) |
| `confluence_pages[]` | Summaries of linked Confluence pages |
| `confluence_details[]` | Per page: `url`, `title`, `has_rich_content`, `image_count`, `has_tables`, `has_lists`, `has_images` |
| `figma_files[]` | Figma collection results |
| `rich_content.has_rich_content` | Whether there is content needing multimodal handling |
| `rich_content.total_images` | Total Confluence image references |
| `rich_content.has_jira_images` | Whether Jira has image attachments |

When stderr shows "rich content detected" or the image count is > 0, the Agent **must** Read the images and process the tables/lists.

## Images

1. **Detect**: Confluence `<ac:image>`, Jira ADF `media`, attachment list, Markdown `![]()`
2. **Download**: platform `fetch_page_by_url.py` uses `--image-dir` by default; for Jira attachments see `image_attachments` from `get_issue.py`
3. **Read**: downloaded images **must be read with the Read tool** for visual recognition
4. **Textualize**: write process steps, UI elements, field definitions and state machines into the requirement understanding
5. **Coverage report**: mark "rules/information obtained from images"

## Fused understanding

1. **Collect**: Jira text + ADF/HTML + Confluence MD + images + Figma
2. **Cross-validate**: consistency of text vs images vs tables
3. **Conflict priority**: JIRA AC > current Confluence PRD > API > Figma > history/knowledge base
4. **Split requirement points**: each rule/screen/flow/constraint -> testable points
5. **Coverage mapping**: mark the source (text/table/image/Figma)

## Confluence wiki markup cleanup

Before generating cases, clean `{LQ}` `{RQ}` `{color}` `{noformat}` etc.; they must not be carried into case bodies.

## Blocker notes

Collection finished but some image references were not downloaded -> record in blockers and continue with what was obtained; if a key image cannot be read and affects AC -> mark as blocked.
