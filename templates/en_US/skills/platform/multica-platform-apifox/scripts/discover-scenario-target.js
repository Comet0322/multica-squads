/**
 * Discover the historical scenario folder of the same module, for mounting supplementary cases.
 * Output: scenario-target.json
 *
 * Strategy (distilled from WS-40):
 * - By default one endpoint belongs to only one scenario (selfHit -> append-existing)
 * - Expanding coverage = appending differentiated steps to that scenario; creating several scenarios for the same endpoint on your own is forbidden
 * - Only when the endpoint has no scenario yet may create-in-same-folder create one
 *
 * Environment variables: APIFOX_PROJECT_ID, APIFOX_ENDPOINT_ID, APIFOX_SOURCE_BRANCH
 */
const path = require('path');
const {
  apifoxJson,
  projectId,
  branchName,
  writeJson,
  ensureTls,
  BASE_URL,
} = require('./lib/apifox');

ensureTls();

const endpointId = process.env.APIFOX_ENDPOINT_ID;
if (!endpointId) {
  console.error('Please set APIFOX_ENDPOINT_ID');
  process.exit(1);
}

const project = projectId();
const branch = branchName();
const common = ['--project', project, '--branch', branch, '--api-base-url', BASE_URL];

function call(args, operation) {
  const result = apifoxJson(args);
  if (!result.success) {
    throw new Error(`${operation} failed: ${result.error?.message || JSON.stringify(result.error)}`);
  }
  return result.data;
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function walk(value, visitor, seen = new Set()) {
  if (!value || typeof value !== 'object' || seen.has(value)) return;
  seen.add(value);
  visitor(value);
  if (Array.isArray(value)) {
    for (const child of value) walk(child, visitor, seen);
  } else {
    for (const child of Object.values(value)) walk(child, visitor, seen);
  }
}

const endpoint = call(['endpoint', 'get', String(endpointId), ...common], 'read endpoint');
const moduleId = endpoint.moduleId;
const endpointName = endpoint.name || `endpoint-${endpointId}`;

const moduleEndpoints = moduleId
  ? asArray(call(['endpoint', 'list', ...common, '--module-id', String(moduleId)], 'list same-module endpoints'))
  : [];
const moduleEndpointIds = new Set(moduleEndpoints.map((item) => String(item.id)));
moduleEndpointIds.add(String(endpointId));

const scenarios = asArray(call(['test-scenario', 'list', ...common], 'list scenarios'));
const candidates = [];

for (const item of scenarios) {
  const full = call(['test-scenario', 'get', String(item.id), ...common], `read scenario ${item.id}`);
  let hitCount = 0;
  let selfHit = false;
  walk(full, (node) => {
    const referenced =
      node.apiDetailId ?? node.endpointId ?? node.httpApiCase?.apiDetailId ?? node.httpApiCase?.id;
    if (!referenced) return;
    const id = String(referenced);
    if (moduleEndpointIds.has(id)) hitCount += 1;
    if (id === String(endpointId)) selfHit = true;
  });
  if (!hitCount && !selfHit) continue;
  candidates.push({
    scenarioId: full.id,
    scenarioName: full.name,
    folderId: full.folderId,
    hitCount,
    selfHit,
  });
}

candidates.sort((a, b) => {
  if (a.selfHit !== b.selfHit) return a.selfHit ? -1 : 1;
  return b.hitCount - a.hitCount;
});

const best = candidates[0] || null;
const selfHitCount = candidates.filter((item) => item.selfHit).length;
const warnings = [];
if (selfHitCount > 1) {
  warnings.push(
    `The same endpoint appears in ${selfHitCount} scenarios: by default append-existing steps to the first-ranked scenario; do not create another scenario for the same endpoint; unless the user explicitly asks, converge on a single scenario`
  );
}

const result = {
  endpointId: Number(endpointId),
  endpointName,
  moduleId,
  branch,
  projectId: Number(project),
  policy: {
    oneEndpointOneScenario: true,
    expandByAppendingSteps: true,
    forbidCreateExtraScenarioWhenSelfHit: true,
    note: 'When the user says "expand the scenario", the default is to add steps to the same scenario, not to create multiple scenarios',
  },
  warnings,
  recommended: best
    ? {
        mode: best.selfHit ? 'append-existing' : 'create-in-same-folder',
        scenarioId: best.selfHit ? best.scenarioId : null,
        folderId: best.folderId,
        scenarioName: best.selfHit ? best.scenarioName : `${endpointName}-automation-supplement`,
        reason: best.selfHit
          ? 'The target endpoint already appears in this scenario: you must append-existing differentiated steps; creating more scenarios for the same endpoint is forbidden'
          : 'No scenario exists for this endpoint yet; you may create [one] supplementary scenario in the same-module historical folder, and later expansion keeps appending to it',
      }
    : {
        mode: 'need-manual-folder',
        scenarioId: null,
        folderId: null,
        scenarioName: `${endpointName}-automation-supplement`,
        reason: 'No same-module historical scenario found; specify scenarioTarget.folderId manually',
      },
  candidates: candidates.slice(0, 20),
};

const outPath =
  process.env.APIFOX_SCENARIO_TARGET_OUT ||
  path.join(process.env.TEMP || '.', `apifox-scenario-target-${endpointId}.json`);
writeJson(outPath, result);
console.log(
  JSON.stringify(
    {
      outPath,
      recommended: result.recommended,
      policy: result.policy,
      warnings: result.warnings,
      candidateCount: candidates.length,
      selfHitCount,
    },
    null,
    2
  )
);
if (!result.recommended.folderId && !result.recommended.scenarioId) process.exitCode = 2;
