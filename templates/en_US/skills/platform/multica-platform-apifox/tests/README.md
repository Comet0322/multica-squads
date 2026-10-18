# Apifox platform skill regression tests

Consolidated from `apifox-test-case-supplement-squad/tests`. Uses the built-in Node.js `node:test` (no npm install needed).

```bash
cd templates/skills/platform/multica-platform-apifox
node --test tests/*.test.js
```

| File | Coverage |
| --- | --- |
| `systems-registry.test.js` | Registry path / exact lookup matching |
| `generator.test.js` | Case generation logic |
| `apifox-lib.test.js` | lib/apifox.js |
| `fixtures/valid-config.json` | Generator fixture |

Optional in CI: run the commands above for this directory from the monorepo root.
