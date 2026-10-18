/**
 * Import single-endpoint test cases into a scenario (the historical location for automation).
 *
 * Dry-run by default; only an explicit --apply writes.
 * Only ai/ branches are allowed.
 *
 * Usage:
 *   node append-to-scenario.js --branch ai/xxx --endpoint-id 3506053 --case-ids 1,2,3
 *   node append-to-scenario.js --branch ai/xxx --endpoint-id 3506053 --manifest <dir>/manifest.json --apply
 *
 * Scenario target (config / environment variables take priority):
 *   APIFOX_SCENARIO_ID  or  scenarioTarget.scenarioId  -> append to an existing scenario
 *   APIFOX_SCENARIO_FOLDER_ID + scenario name         -> look for the same name in that folder; create it if absent
 */
const fs = require('fs');
const path = require('path');
const {
  apifoxJson,
  projectId,
  writeJson,
  ensureTls,
  BASE_URL,
} = require('./lib/apifox');

ensureTls();

function arg(name, def) {
  const i = process.argv.indexOf(name);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  return def;
}

function die(message) {
  console.error(message);
  process.exit(1);
}

const branch = arg('--branch', process.env.APIFOX_BRANCH);
const endpointId = String(arg('--endpoint-id', process.env.APIFOX_ENDPOINT_ID || ''));
const apply = process.argv.includes('--apply');
const manifestPath = arg('--manifest', '');
const caseIdsArg = arg('--case-ids', '');
const scenarioIdArg = arg('--scenario-id', process.env.APIFOX_SCENARIO_ID || '');
const folderIdArg = arg('--folder-id', process.env.APIFOX_SCENARIO_FOLDER_ID || '');
const scenarioNameArg = arg('--scenario-name', process.env.APIFOX_SCENARIO_NAME || '');
const configPath = arg('--config', path.join(__dirname, 'config.json'));

if (!branch) die('Missing --branch');
if (!branch.startsWith('ai/')) die(`Branch "${branch}" refused: only ai/ branches are allowed`);
if (!endpointId) die('Missing --endpoint-id');

let config = {};
if (fs.existsSync(configPath)) {
  config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
}
const scenarioTarget = config.scenarioTarget || {};

const project = projectId();
const common = ['--project', project, '--branch', branch, '--api-base-url', BASE_URL];

function call(args, operation) {
  const result = apifoxJson(args);
  if (!result.success) {
    die(`${operation} failed: ${result.error?.message || JSON.stringify(result.error)}`);
  }
  return result.data;
}

function parseCaseIds() {
  if (caseIdsArg) {
    return caseIdsArg
      .split(',')
      .map((id) => id.trim())
      .filter(Boolean);
  }
  if (manifestPath) {
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    const created = Array.isArray(manifest.created) ? manifest.created : [];
    const ids = created.map((item) => String(item.id || item)).filter(Boolean);
    if (!ids.length) die(`manifest contains no created cases: ${manifestPath}`);
    return ids;
  }
  die('Provide --case-ids or --manifest');
}

function resolveScenarioMeta() {
  const scenarioId = scenarioIdArg || scenarioTarget.scenarioId || '';
  const folderId = folderIdArg || scenarioTarget.folderId || '';
  const scenarioName =
    scenarioNameArg ||
    scenarioTarget.scenarioName ||
    `${config.namePrefix || 'endpoint'}-automation-supplement`;

  if (scenarioId) {
    return { mode: 'append', scenarioId: String(scenarioId), folderId: folderId || null, scenarioName };
  }
  if (!folderId) {
    die(
      'Missing scenario target: set scenarioTarget.scenarioId, or scenarioTarget.folderId + scenarioName.\n' +
        'folderId should come from the folder of historical scenarios in the same module, so new cases sit in the same directory tree as the historical cases.'
    );
  }
  return { mode: 'find-or-create', scenarioId: null, folderId: String(folderId), scenarioName };
}

function listScenariosInFolder(folderId) {
  const all = call(['test-scenario', 'list', ...common], 'list scenarios') || [];
  return (Array.isArray(all) ? all : []).filter((item) => String(item.folderId) === String(folderId));
}

function getScenario(id) {
  return call(['test-scenario', 'get', String(id), ...common], `read scenario ${id}`);
}

function existingBoundCaseIds(scenario) {
  const ids = new Set();
  const walk = (node) => {
    if (!node || typeof node !== 'object') return;
    if (Array.isArray(node)) {
      node.forEach(walk);
      return;
    }
    const bound =
      node.testCaseId ||
      node.httpApiCase?.testCaseId ||
      node.bindTestCaseId ||
      (node.bindType === 'TEST_CASE' && (node.bindId || node.resourceId));
    if (bound) ids.add(String(bound));
    Object.values(node).forEach(walk);
  };
  walk(scenario.steps || scenario);
  return ids;
}

const caseIds = parseCaseIds();
const target = resolveScenarioMeta();

let scenarioId = target.scenarioId;
let createdScenario = false;

if (!scenarioId) {
  const listed = listScenariosInFolder(target.folderId);
  const hit = listed.find((item) => item.name === target.scenarioName);
  if (hit) {
    scenarioId = String(hit.id);
  } else if (apply) {
    const created = call(
      [
        'test-scenario',
        'create',
        ...common,
        '--name',
        target.scenarioName,
        '--folder-id',
        target.folderId,
        '--priority',
        String(scenarioTarget.priority ?? 2),
      ],
      'create scenario'
    );
    scenarioId = String(created.id || created.scenarioId || created);
    createdScenario = true;
  } else {
    console.log(
      JSON.stringify(
        {
          dryRun: true,
          action: 'would-create-scenario',
          folderId: target.folderId,
          scenarioName: target.scenarioName,
          caseIds,
          endpointId,
        },
        null,
        2
      )
    );
    process.exit(0);
  }
}

const scenario = getScenario(scenarioId);
const already = existingBoundCaseIds(scenario);
const toImport = caseIds.filter((id) => !already.has(String(id)));
const skipped = caseIds.filter((id) => already.has(String(id)));

console.log(
  JSON.stringify(
    {
      dryRun: !apply,
      branch,
      endpointId,
      scenarioId,
      scenarioName: scenario.name || target.scenarioName,
      folderId: scenario.folderId || target.folderId,
      createdScenario,
      total: caseIds.length,
      toImport,
      skipped,
    },
    null,
    2
  )
);

if (!apply) {
  console.log('DRY-RUN complete; after confirming, re-run with --apply');
  process.exit(0);
}

if (!toImport.length) {
  console.log('No cases to import (all are already bound to this scenario)');
  process.exit(0);
}

const imported = call(
  [
    'test-scenario',
    'import-steps',
    String(scenarioId),
    ...common,
    '--source',
    'test-case',
    '--endpoint',
    String(endpointId),
    '--ids',
    toImport.join(','),
    '--sync',
    'manual',
  ],
  'import cases into scenario'
);

const outPath =
  process.env.APIFOX_SCENARIO_OUT ||
  path.join(process.env.TEMP || '.', `apifox-scenario-append-${scenarioId}.json`);
writeJson(outPath, {
  ok: true,
  branch,
  scenarioId,
  endpointId,
  importedCaseIds: toImport,
  skippedCaseIds: skipped,
  createdScenario,
  result: imported,
});
console.log(JSON.stringify({ ok: true, outPath, scenarioId, imported: toImport.length }, null, 2));
