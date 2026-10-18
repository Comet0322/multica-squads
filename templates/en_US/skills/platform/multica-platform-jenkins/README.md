# multica-platform-jenkins Usage Guide

Jenkins platform shell: trigger build / release / promotion pipelines. All URLs and credentials are placeholders; fill in your own Jenkins address in `.env`.

## 1. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in:
#   JENKINS_URL=http://your-jenkins.example.com:8080
#   JENKINS_USER=<your-user>
#   JENKINS_PASSWORD=<your-pass>
```

You can also set `jenkins.url`, the login mode (`api-token` / `basic`), and `curl_resolve` in `config.yaml` (if you need to pin internal DNS resolution, use `<JENKINS_URL>:<JENKINS_INTERNAL_IP>`).

## 2. Install dependencies

```bash
cd scripts
pip install -r requirements.txt   # requests only
```

## 3. Main scripts

| Script | Purpose | Example |
|---|---|---|
| `trigger_env.py` | Trigger a dev or sit build by issue / service / branch | `python scripts/trigger_env.py --env sit --service <service1>,<service2> --branch release/<ISSUE_KEY>-xxx --json` |
| `build_sit.py` | Trigger a build in the sit environment | `python scripts/build_sit.py --service <service>` |
| `promote_prod.py` | Promote a sit build to prod (with two-person review) | `python scripts/promote_prod.py --job <JENKINS_JOB_NAME> --build <BUILD_ID>` |
| `list_jobs.py` | List the jobs in the catalog | `python scripts/list_jobs.py` |
| `validate.py` | Validate parameters / branch naming | `python scripts/validate.py --env sit --issue <ISSUE_KEY>` |

> The job list is in `jobs-catalog.yaml` (sanitized into a placeholder skeleton); fill in your own "service name -> full Jenkins job name" mapping.

## 4. Notes

- All real addresses, IPs and job names are placeholders; **do not commit real values**.
- Promotion to production requires two-person review; the scripts do not bypass that gate.
