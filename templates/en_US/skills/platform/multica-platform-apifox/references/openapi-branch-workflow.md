# OpenAPI Sync · AI Branch Workflow

**Applies to**: `sync_openapi.js` (called by @BackendDev via `multica-artifact-backend`).  
**Difference from scenario supplement**: endpoint **definition** sync creates a new branch every time; scenario **case** supplements (see `reference.md` § AI branch policy) may reuse the branch of the same Issue.

---

## Mandatory rules

| Rule | Description |
| --- | --- |
| **Never write directly to main** | OpenAPI import, tagging and orphan deletion must run on an AI branch |
| **New branch for every sync** | Every time `openapi.json` is published/changed for the same Issue and synced to Apifox, you **must** `branch create` a new AI branch; do not reuse a branch that was already merged in a previous round |
| **Branch naming** | `ai/<ISSUE-KEY>-openapi-<YYYYMMDD>`; for several syncs on the same day, increment `-r2`, `-r3` |
| **Merge** | By default a human merges (`branch merge`) after review in the Apifox client; the Agent must not merge into main on its own (unless the Leader authorizes it in writing) |

---

## Standard steps (every Backend contract sync)

### 1. Resolve the project

```bash
node scripts/systems-registry.js lookup --name "<system-name>"
# or the user provides APIFOX_PROJECT_ID
```

### 2. Create the AI branch

```bash
export APIFOX_PROJECT_ID=<id>
export APIFOX_ACCESS_TOKEN=<token>

# Example branch name: ai/CDS2-1813-openapi-20260902
BRANCH="ai/<ISSUE-KEY>-openapi-$(date +%Y%m%d)"
apifox branch create --project $APIFOX_PROJECT_ID --name "$BRANCH" \
  --from main --type ai --api-base-url https://apifox.example.com
```

If the same name already exists (repeated sync on the same day), use `ai/<ISSUE-KEY>-openapi-<YYYYMMDD>-r2` instead.

### 3. Sync OpenAPI on the branch

```bash
node scripts/sync_openapi.js \
  --file docs/backend/<ISSUE-KEY>/openapi.json \
  --issue <ISSUE-KEY> \
  --tag <ISSUE-KEY> \
  --branch "$BRANCH" \
  --json
```

### 4. Report evidence

Write into the API contract revision record / Leader comment:

- AI branch name
- JSON summary of `sync_openapi.js` (imported / tagged / deleted)
- If not merged, note "pending merge after human review"

### 5. (Optional) Merge into main

```bash
apifox branch merge --project $APIFOX_PROJECT_ID --type ai \
  --from "$BRANCH" --to main \
  --api-base-url https://apifox.example.com
```

On merge 422001 (AI write not enabled on main) -> merge in the Apifox **client**, see `reference.md`.

---

## Tester parallel scenario supplement

When T1 writes endpoint scenarios:

1. Prefer to **pick-to** the endpoints already synced on this Issue's OpenAPI branch (`ai/<ISSUE-KEY>-openapi-*`)  
2. If Backend has not synced yet, the Tester may create `ai/<ISSUE-KEY>-scenarios-<YYYYMMDD>` under the same naming rule, but **must not** create cases on main  
3. After an OpenAPI change, Backend creates a new openapi branch -> the Tester `pick-to` the new branch and then supplements scenarios

---

## Environment variables

| Variable | Purpose |
| --- | --- |
| `APIFOX_SOURCE_BRANCH` | Only the **create --from** source branch, default `main`; **not** the sync target branch |
| `--branch` / `APIFOX_BRANCH` | The **target** AI branch of this sync (required; omitting it and falling back to main is forbidden) |

---

## Common mistakes

| Symptom | Action |
| --- | --- |
| Omitted `--branch`, wrote to main | Stop; create a new AI branch and rerun the sync |
| Reused an already-merged old branch for a second OpenAPI change | Violation; a new branch must be created |
| Endpoint not visible in list after create | Confirm that sync and create use the same `--branch` |
