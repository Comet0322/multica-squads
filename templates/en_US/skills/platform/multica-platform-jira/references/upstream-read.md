# Upstream Read Specification (JIRA + Linked Issues + Confluence)

Every **producer role** (PM / Architect / Designer / Frontend / Backend / Tester) runs this before starting work.

---

## Order (no skipping steps)

| Step | Action | Tool |
| --- | --- | --- |
| 1 | Read the **current Issue** JSON | `get_issue.py` or `jira_cli.py get-issue` |
| 2 | Read **`linked_issues`**; pick the **must-read** links per the Issue's "References" or the Leader's G0 notes | same as above; optional `--with-linked` |
| 3 | Resolve the **Issue Hub** (the first Confluence pageId) | `get-confluence-url` / `resolve-parent-page-id` |
| 4 | Read the PRD / existing child pages (design, contract, T1/T2) | `multica-platform-confluence` `fetch_page.py` |
| 5 | Read the **Figma** links in the description (Designer/Tester/Frontend) | `multica-platform-figma` |
| 6 | Information still insufficient | **BLOCKED** + open items; **no guessing** |

---

## Which linked Issues count as "must-read"

**Must-read** by default (unless the Issue or Leader explicitly says "ignore"):

- `Relates` / `Clone` (and their localized equivalents)
- The **blocked party** of `Blocks` (what is blocking the current Issue)
- KEYs **named explicitly** in the Issue description or "References"

Optional:

- A distant Epic (only when the PM provided no separate PRD link and the Leader asks to trace the Epic)

---

## `--with-linked` behavior

```bash
python scripts/get_issue.py --url "<JIRA_URL>" --with-linked -o data/jira-full.json
```

In addition to the current Issue, the output adds `linked_issues_detail[]`: each item contains `key`, `summary`, `description_text` and `links` (Confluence/Figma).

**Agent obligation**: for each must-read item in `linked_issues_detail`, `fetch_page` every entry in its `links.confluence[]`; list the KEY + link in the "Upstream references" section of the deliverable.

---

## How to reference upstream in deliverables

| Deliverable | Reference wording |
| --- | --- |
| PRD | "Related requirement PROJ-100: [link]; differences in this requirement: ..." |
| Architecture design | "Builds on the increment in PROJ-100 design section 3; see the link for unchanged parts" |
| API contract | "Inherits PROJ-100 API-ID x-y; new API-IDs in this requirement ..." |
| T1/T2 | "Regression of PROJ-100 CASE-xxx; new CASE-... in this requirement" |

---

## Relationship to the knowledge base (KB)

The `team knowledge base (optional)` is only for **Step 0.5 background/terminology**; it **does not replace** reading the body of linked JIRA/Confluence content. KB answers must be labeled "KB reference, not an AC source" in the deliverable.

---

## Common failure modes

| Bad | Better |
| --- | --- |
| Start coding after reading only the current Issue title | get-issue + linked + read Confluence fully before starting |
| Copy a linked Story's ACs wholesale into the current PRD | State clearly which ACs are inherited vs. new |
| Assume no history because linked_issues is empty | Still read the Issue Hub child pages (there may be manually added URLs that are not linked) |
