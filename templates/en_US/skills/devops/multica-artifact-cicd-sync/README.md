# multica-artifact-cicd-sync usage

CI/CD landing orchestration skill: turns a code-review verdict into Jenkins trigger parameters and calls **`multica-platform-jenkins`** to run the build / release.

## 1. Prerequisites

- `multica-platform-jenkins` is mounted (it provides the Jenkins URL and credentials).
- `issue_service_map` in this skill's `config.yaml` is a placeholder example; fill it in with your own "Issue prefix -> services to trigger" mapping.

## 2. Configuration

```bash
cp .env.example .env
# Usually no extra variables are needed; Jenkins credentials come from multica-platform-jenkins/.env
```

## 3. Install dependencies

```bash
cd scripts
pip install -r requirements.txt   # PyYAML only
```

## 4. Main scripts

| Script | Purpose | Example |
|---|---|---|
| `trigger_cicd.py` | Trigger CI/CD for the matching service(s) based on the review verdict | `python scripts/trigger_cicd.py --issue <ISSUE_KEY> --env sit --service <service>` |
| `resolve_skills.py` | Resolve the paths of the platform skills this skill depends on | imported by `trigger_cicd.py` |
| `validate.py` | Validate inputs / configuration | `python scripts/validate.py` |

## 5. Notes

- The prefixes in `issue_service_map` in `config.yaml` (`<ISSUE_PREFIX_A>`, etc.) are placeholders; replace them with your team's conventions.
- Put real Jenkins addresses / job names in `multica-platform-jenkins`; this skill holds no infrastructure information.
