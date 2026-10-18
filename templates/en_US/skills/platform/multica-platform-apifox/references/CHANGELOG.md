# Changelog (Apifox endpoint scenario supplement)

> Consolidated from the `apifox-test-case-supplement-squad` version history; this is the authority for platform skill script behavior.

## 1.4.9

- Multi-user, multi-project: task cards, configurable registry path, isolation per OPERATOR
- Empty registry template for Skill distribution; runtime/private files are gitignored
- config.example is all placeholders; do not copy real project IDs
- AI branches are reused per operator; ask first on cross-user conflicts; concurrency check before scenario import
- Copyable MULTICA instructions (no local absolute paths)

## 1.4.8

- Project IDs must not be hard-coded as an example list; only user input / exact registry hit / unique match by name
- systems-registry lookup no longer does fuzzy includes

## 1.4.7

- One scenario per endpoint (WS-40); assertion quality constraints
