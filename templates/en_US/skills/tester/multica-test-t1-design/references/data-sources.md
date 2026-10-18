# Test Data Collection Orchestration Guide (T1 collection)

> **Platform collaboration**: JIRA / Confluence / Figma read/write goes through `multica-platform-jira`, `multica-platform-confluence`, `multica-platform-figma`.  
> This document describes **T1 `fetch_all.py` orchestration** and credential priority.

## Overview

Collection chain: Jira Issue -> Confluence requirement -> Figma design -> case-generation material.

---

## 1. Authentication configuration

### Jira & Confluence (by priority)

```bash
# Option 1 (recommended): domain account — your-domain.atlassian.net / your-domain.atlassian.net/wiki
export JIRA_USERNAME="your_domain_account"
export JIRA_PASSWORD="your_domain_password"

# Option 2: self-hosted Jira username/password
export JIRA_USERNAME="your_username"
export JIRA_PASSWORD="your_password"

# Option 3: Atlassian Cloud
export JIRA_EMAIL="your.name@company.com"
export JIRA_API_TOKEN="your_atlassian_api_token"

# Option 4 (fallback): Cookie
export JIRA_COOKIE="JSESSIONID=xxx"
export CONFLUENCE_COOKIE="JSESSIONID=xxx"
```

> **Priority**: `JIRA_USERNAME / JIRA_PASSWORD` = `JIRA_USERNAME/PASSWORD` > Cloud Email+Token > Cookie. Consistent with `AGENTS.md` and `multica-platform-jira`.  
> You can also copy `config.local.env.example` -> `config.local.env` (do not commit).

### Figma

```bash
export FIGMA_TOKEN="figd_xxxxx_your_figma_token"
```

### Team knowledge base (Step 0.5b)

```bash
export TEAM_KB_URL="https://team-kb.example.com"   # optional, default see platform config
export TEAM_KB_TIMEOUT=600                         # optional, seconds
export TEAM_KB_INTERVAL=2                          # optional, seconds
```

Invocation: the team knowledge-base Q&A script (optional, not shipped with this repo).

---

## 2. Supported input formats

### Jira Issue URL

```
# Standard format
https://your-domain.atlassian.net/browse/PROJ-123

# Format with query parameters
https://your-domain.atlassian.net/browse/PROJ-123?atlOrigin=...
```

**The Jira description should contain at least one of the following (used to extract links):**
- Confluence page link (requirement document)
- Figma file link (UI design)

### Confluence URL

```
# Page format
https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title
https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456

# Space home format (must be used together with the page title)
https://your-domain.atlassian.net/wiki/spaces/SPACE/overview
```

**Extracted content:**
- Page title and version info
- Body content (automatically converted to Markdown)
- Table data (structured extraction)
- Child page content (optional: --include-children)

### Figma URL

```
# New Design URL
https://www.figma.com/design/ABC123def/Page-Name

# Legacy File URL
https://www.figma.com/file/ABC123def/Page-Name

# Specific node
https://www.figma.com/file/ABC123def/Page-Name?node-id=0-1

# Prototype URL
https://www.figma.com/proto/ABC123def/Page-Name
```

**Extracted content:**
- File and page structure (Canvas -> Frame -> elements)
- Component definitions (COMPONENT / COMPONENT_SET)
- Style definitions (colors, text, etc.)
- Text content and style information
- Interaction settings (click-through, etc.)
- Element size and position

---

## 3. Data flow architecture

```
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│             │    │                 │    │              │
│  Jira Issue ├────► Confluence URL ├────► Requirement  │
│             │    │                 │    │  doc (MD)    │
└──────┬──────┘    └─────────────────┘    └──────────────┘
       │                                        │
       │                                  ┌─────▼──────┐
       │                                  │              │
       ├────► Figma URL ─────────────────► Design (JSON)│
       │                                  │              │
       │                                  └──────────────┘
       │                                        │
       │                                  ┌─────▼──────┐
       └──────────────────────────────────►  Aggregated  │
                                          │ data (JSON) │
                                          └──────────────┘
```

**Collection script call flow (run inside Claude Code):**

```bash
# Option 1: collect everything in one go
cd /path/to/test-case-generator
python scripts/fetch_all.py \
  --jira-url "https://your-domain.atlassian.net/browse/PROJ-123" \
  --output-dir ./data

# Option 2: step by step (platform CLI)
# Step 1: JIRA Issue
python multica-platform-jira/scripts/get_issue.py \
  --url "https://your-domain.atlassian.net/browse/PROJ-123" \
  --output ./data/jira_issue.json

# Step 2: Confluence
python multica-platform-confluence/scripts/fetch_page_by_url.py \
  --url "https://your-domain.atlassian.net/wiki/spaces/SP/pages/123" \
  --output ./data/requirements.md \
  --json ./data/requirements.json

# Step 3: Figma
python multica-platform-figma/scripts/fetch_file.py \
  --url "https://www.figma.com/design/ABC123/Page-Name" \
  --output ./data/figma.json \
  --summary ./data/figma_summary.txt
```

---

## 4. Permission requirements

### Jira API
- **Browse Projects** permission on the target project
- Ability to read the Issue's description and custom fields

### Confluence API
- **View** permission on the target space
- `api/v2/pages/{id}` — read page content and child pages

### Figma API
- The user needs **View** permission on the file (the file is shared with the Token holder via a share link)
- A Figma Personal Access Token is required

---

## 5. Notes

1. **Privacy and security**: do not commit API tokens to version control. Prefer environment variables or configure them in a `.env` file (already in `.gitignore`)
2. **Network requirements**: the Atlassian and Figma API endpoints must be reachable. A corporate intranet may require a VPN
3. **Rate limits**: Atlassian APIs are rate limited (typically 100 requests/minute); Figma is more lenient
4. **Large files**: very large Figma files may take a long time to collect; the script sets a 60-second timeout
5. **Images**: Figma images must be fetched separately via the `images` API; the script provides exported support for the related functions
