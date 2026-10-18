# Jenkins CI/CD Reference (cicd space · dev / sit)

> Full job catalog: `jobs-catalog.yaml`(logical `service` -> `<jenkins-job-dev-pattern>` / `<jenkins-job-sit-pattern>` / `<jenkins-job-crm-dev-pattern>`)

## Environments

| Environment | Job naming | Example |
| --- | --- | --- |
| dev | `<jenkins-job-dev-service>` / `<jenkins-job-crm-dev-service>` | `<jenkins-job-dev-example>` |
| sit | `<jenkins-job-sit-service>` | `<jenkins-job-sit-example>` |

Base URL：`http://<JENKINS_URL>`

## Common commands

```bash
# List all triggerable sit services
python scripts/list_jobs.py --env sit

# Look up the job name for a single service
python scripts/list_jobs.py --env dev --service <service>

# Trigger dev / sit (deploy branch, not feature)
python scripts/trigger_env.py --env dev --service <service> --branch release/<ISSUE_KEY>-xxx

python scripts/trigger_env.py --env sit --service <service1>,<service2> --branch release/<ISSUE_KEY>-xxx --json
```

## Orchestration (Multica DevOps)

```bash
python ../multica-artifact-cicd-sync/scripts/trigger_cicd.py \
  --issue <ISSUE_KEY> --env dev --service <service> --branch release/<ISSUE_KEY>-xxx --json
```

`issue_service_map` is configured with the `<ISSUE_PREFIX_A>` / `<ISSUE_PREFIX_B>` / `<ISSUE_PREFIX_C>` / `<ISSUE_PREFIX_D>` prefixes, so you can pass only `--issue` without `--service`.

## Naming inconsistencies (recorded in the catalog)

| service | dev | sit |
| --- | --- | --- |
| apisix-v3 | <jenkins-job-dev-example-1> | <jenkins-job-sit-example-1> |
| <service-gw-jurisdiction> | <jenkins-job-dev-example>_gw_jurisdiction_service | <jenkins-job-sit-example-2> |
| pmm-report-generator | <jenkins-job-dev-example-3> | <jenkins-job-sit-example-3> |
| modelService | <jenkins-job-dev-example-4> | <jenkins-job-sit-example-4> |

## Build displayName patterns (reference)

- dev：`{build}_{module}_{branch}_dev_{version}`
- sit：`{build}_{module}_{branch}_sit_{version}` or `deployVersion_sit_{version}`

## Parameters

**Default**: copy all parameters from the job's most recent **SUCCESS** build and override **only** branch-type parameters (branchName / branch / gitBranch ...) with `--branch`. `--param` can override any item; `--no-last-success` turns off the seeding behavior.

```bash
# Discover (view last_success + resolved)
python scripts/trigger_env.py --env sit --service <service> --branch feature/foo --discover-only --json

# Trigger (deployVersion / env etc. carry over from the last SUCCESS)
python scripts/trigger_env.py --env sit --service <service> --branch feature/foo --json

# Manually override a single parameter
python scripts/trigger_env.py --env sit --service <service> --branch feature/foo --param deployVersion=1.75.0_795 --json
```

## Cross-platform

Python 3; commands are identical on Windows / Linux. JIRA write-back still requires bash.






