/**
 * Auth pre-processor discovery (read-only, strictly scoped to the "current project + target module").
 *
 * Hard rules:
 * - Never hard-code script IDs (different projects/modules may differ completely)
 * - Never auto-adopt across modules
 * - Must copy verbatim from historical cases/scenarios of the same moduleId via with-case-detail
 * - commonScript IDs must be resolvable in the current project's common-script list
 * - Script-library keywords only produce a candidate list and are never written automatically
 */
const path = require('path');
const {
  apifoxJson,
  projectId,
  branchName,
  writeJson,
  ensureTls,
} = require('./lib/apifox');

ensureTls();

const endpointId = process.env.APIFOX_ENDPOINT_ID;
const preferredScenarioId = process.env.APIFOX_SCENARIO_ID || '';
if (!endpointId) {
  console.error('Please set APIFOX_ENDPOINT_ID');
  process.exit(1);
}

const branch = branchName();
const project = projectId();
// Matches auth step names. \u767b\u5f55 / \u9274\u6743 / \u8ba4\u8bc1 are the Chinese words for "login" / "authentication" / "authorization"
// (kept as escapes because real Apifox step names in Chinese projects use them).
const AUTH_STEP_NAME = /\u767b\u5f55|\u9274\u6743|\u8ba4\u8bc1|login|authenticat|cookie|ticket|session|getCookie/i;

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

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

const endpoint = call(
  [
    'endpoint',
    'get',
    String(endpointId),
    '--project',
    project,
    '--branch',
    branch,
    '--api-base-url',
    'https://apifox.example.com',
  ],
  'read target endpoint'
);

const moduleId = endpoint.moduleId;
const folderId = endpoint.folderId;
if (!moduleId) {
  console.error('The target endpoint has no moduleId; module-level auth discovery is impossible');
  process.exit(1);
}

const scripts = asArray(
  call(['common-script', 'list', '--project', project, '--api-base-url', 'https://apifox.example.com'], 'read current project script library')
);
const scriptById = new Map(scripts.map((script) => [String(script.id), script]));

const moduleEndpoints = asArray(
  call(
    [
      'endpoint',
      'list',
      '--project',
      project,
      '--branch',
      branch,
      '--module-id',
      String(moduleId),
      '--api-base-url',
      'https://apifox.example.com',
    ],
    `list same-module endpoints moduleId=${moduleId}`
  )
);
const moduleEndpointIds = new Set(moduleEndpoints.map((item) => String(item.id)));
moduleEndpointIds.add(String(endpointId));

function validateCommonScriptIds(preProcessors) {
  const unknown = [];
  const resolved = [];
  for (const processor of asArray(preProcessors)) {
    if (processor.type !== 'commonScript' || !Array.isArray(processor.data)) continue;
    for (const id of processor.data) {
      const key = String(id);
      const script = scriptById.get(key);
      if (!script) unknown.push(key);
      else resolved.push({ id: script.id, name: script.name });
    }
  }
  return { unknown, resolved };
}

/**
 * A same-module historical pre-processor is itself the evidence: the script name need not contain a "login" keyword.
 * As long as preProcessors is non-empty and the script ID resolves in this project, it can be a candidate.
 */
function analyzePreProcessors(preProcessors) {
  const cleaned = asArray(preProcessors)
    .filter((processor) => processor && processor.type && processor.type !== 'placeholder')
    .map(deepClone);
  if (!cleaned.length) return null;

  const { unknown, resolved } = validateCommonScriptIds(cleaned);
  if (unknown.length) {
    return { rejected: true, unknown, cleaned: null, resolvedScripts: [] };
  }

  const hasCommonOrCustom = cleaned.some(
    (processor) => processor.type === 'commonScript' || processor.type === 'customScript'
  );
  if (!hasCommonOrCustom) return null;

  return {
    rejected: false,
    cleaned,
    resolvedScripts: resolved,
    reasons: cleaned.map((processor) => {
      if (processor.type === 'commonScript') {
        return `commonScript:${(processor.data || [])
          .map((id) => scriptById.get(String(id))?.name || id)
          .join(',')}`;
      }
      return processor.type;
    }),
  };
}

const result = {
  endpointId: Number(endpointId),
  moduleId,
  folderId,
  branch,
  projectId: Number(project),
  preferredScenarioId: preferredScenarioId || null,
  authPreProcessors: null,
  scenarioAuthHttpSteps: [],
  source: null,
  confidence: 'none',
  requiresConfirmation: true,
  validatedScripts: [],
  candidates: [],
  // Display only; never adopted automatically
  scriptLibraryCandidates: scripts.map((script) => ({ scriptId: script.id, scriptName: script.name })),
  warnings: [],
  policy: {
    scope: 'same-project + same-module only',
    hardCodeScriptIds: false,
    crossModuleAutoAdopt: false,
    scriptLibraryAutoAdopt: false,
  },
};

function addCandidate(item) {
  if (!moduleEndpointIds.has(String(item.endpointId || endpointId)) && item.source !== 'target-scenario') {
    // Discard any source that is not an endpoint of this module
    if (item.endpointId && !moduleEndpointIds.has(String(item.endpointId))) return;
  }

  const confidence =
    item.source === 'target-scenario-same-endpoint'
      ? 'high'
      : item.source === 'target-scenario'
        ? 'high'
        : item.source === 'same-endpoint'
          ? 'high'
          : item.source === 'same-folder'
            ? 'medium'
            : item.source === 'same-module' || item.source === 'module-scenario'
              ? 'medium'
              : 'low';

  // Cross-module items should never get here; if one does, force low confidence + require confirmation and do not recommend by default
  if (item.crossModule) return;

  result.candidates.push({ ...item, confidence });
}

function casesOnEndpoint(sourceEndpointId, source) {
  if (!moduleEndpointIds.has(String(sourceEndpointId))) return;

  const listed = asArray(
    call(
      [
        'test-case',
        'list',
        '--project',
        project,
        '--branch',
        branch,
        '--endpoint',
        String(sourceEndpointId),
        '--api-base-url',
        'https://apifox.example.com',
      ],
      `list cases of same-module endpoint ${sourceEndpointId}`
    )
  );

  for (const item of listed) {
    const full = call(
      [
        'test-case',
        'get',
        String(item.id),
        '--project',
        project,
        '--branch',
        branch,
        '--api-base-url',
        'https://apifox.example.com',
      ],
      `read case ${item.id}`
    );
    const analyzed = analyzePreProcessors(full.preProcessors);
    if (!analyzed) continue;
    if (analyzed.rejected) {
      result.warnings.push({
        type: 'unknown-script-id',
        caseId: full.id,
        caseName: full.name,
        unknown: analyzed.unknown,
      });
      continue;
    }
    addCandidate({
      source,
      endpointId: sourceEndpointId,
      caseId: full.id,
      caseName: full.name,
      preProcessors: analyzed.cleaned,
      reasons: analyzed.reasons,
      resolvedScripts: analyzed.resolvedScripts,
    });
  }
}

function collectFromScenario(scenarioId, sourceHint) {
  const full = call(
    [
      'test-scenario',
      'get',
      String(scenarioId),
      '--project',
      project,
      '--branch',
      branch,
      '--with-case-detail',
      '--api-base-url',
      'https://apifox.example.com',
    ],
    `read scenario ${scenarioId} (with-case-detail)`
  );

  let referencesTarget = false;
  let referencesModule = false;
  const authHttpSteps = [];

  for (const step of asArray(full.steps)) {
    const caseObj = step.httpApiCase || {};
    const apiId = caseObj.apiDetailId ?? step.apiDetailId;
    if (apiId && String(apiId) === String(endpointId)) referencesTarget = true;
    if (apiId && moduleEndpointIds.has(String(apiId))) referencesModule = true;

    if (AUTH_STEP_NAME.test(step.name || '') || AUTH_STEP_NAME.test(caseObj.name || '')) {
      authHttpSteps.push({
        name: step.name,
        apiDetailId: apiId || null,
        method: caseObj.method || null,
        path: caseObj.path || null,
      });
    }

    // Skip auth-endpoint-type steps themselves (they usually have no business script); take the pre-processors of their sibling business steps
    if (AUTH_STEP_NAME.test(step.name || '') && !(caseObj.preProcessors || []).some((p) => p?.type === 'commonScript')) {
      continue;
    }

    const analyzed = analyzePreProcessors(caseObj.preProcessors || step.preProcessors);
    if (!analyzed) continue;
    if (analyzed.rejected) {
      result.warnings.push({
        type: 'unknown-script-id',
        scenarioId: full.id,
        stepName: step.name,
        unknown: analyzed.unknown,
      });
      continue;
    }

    let source = sourceHint;
    if (apiId && String(apiId) === String(endpointId)) source = 'target-scenario-same-endpoint';
    else if (sourceHint === 'target-scenario') source = 'target-scenario';
    else if (apiId && moduleEndpointIds.has(String(apiId))) source = 'module-scenario';
    else continue; // The scenario step does not belong to an endpoint of this module -> discard

    addCandidate({
      source,
      scenarioId: full.id,
      scenarioName: full.name,
      stepName: step.name,
      endpointId: apiId,
      preProcessors: analyzed.cleaned,
      reasons: analyzed.reasons,
      resolvedScripts: analyzed.resolvedScripts,
    });
  }

  if (authHttpSteps.length && (referencesTarget || referencesModule)) {
    result.scenarioAuthHttpSteps.push({
      scenarioId: full.id,
      scenarioName: full.name,
      steps: authHttpSteps,
      note: 'The same-module scenario contains a standalone auth HTTP step; supplementary business steps must keep this pattern and copy the preProcessors of sibling business steps in the same module',
    });
  }

  return { referencesTarget, referencesModule, full };
}

// 1) Cases of this endpoint
casesOnEndpoint(Number(endpointId), 'same-endpoint');

// 2) Cases of other endpoints in the same module (same-folder ones are flagged first)
for (const item of moduleEndpoints) {
  if (String(item.id) === String(endpointId)) continue;
  const source = String(item.folderId) === String(folderId) ? 'same-folder' : 'same-module';
  casesOnEndpoint(item.id, source);
}

// 3) The designated target scenario takes priority
if (preferredScenarioId) {
  collectFromScenario(preferredScenarioId, 'target-scenario');
}

// 4) Scan scenarios, but keep only those that reference endpoints of this module
const scenarios = asArray(
  call(
    ['test-scenario', 'list', '--project', project, '--branch', branch, '--api-base-url', 'https://apifox.example.com'],
    'list test scenarios'
  )
);
for (const item of scenarios) {
  if (preferredScenarioId && String(item.id) === String(preferredScenarioId)) continue;
  const before = result.candidates.length;
  const { referencesTarget, referencesModule } = collectFromScenario(item.id, 'module-scenario');
  if (!referencesTarget && !referencesModule) {
    result.candidates = result.candidates.slice(0, before);
  }
}

function score(candidate) {
  const sourceScore = {
    'target-scenario-same-endpoint': 600,
    'target-scenario': 500,
    'same-endpoint': 450,
    'same-folder': 300,
    'same-module': 220,
    'module-scenario': 180,
  }[candidate.source] || 0;
  const sameEndpointBonus =
    candidate.endpointId && String(candidate.endpointId) === String(endpointId) ? 40 : 0;
  const signature = JSON.stringify(candidate.preProcessors);
  const frequency = result.candidates.filter((other) => JSON.stringify(other.preProcessors) === signature)
    .length;
  return sourceScore + sameEndpointBonus + frequency;
}

const ranked = [...result.candidates].sort((a, b) => score(b) - score(a));
if (ranked.length) {
  const best = ranked[0];
  const { unknown, resolved } = validateCommonScriptIds(best.preProcessors);
  if (unknown.length) {
    result.warnings.push({
      fatal: true,
      message: `The recommended auth contains script IDs that do not exist in the current project: ${unknown.join(',')}`,
    });
  } else {
    result.authPreProcessors = best.preProcessors;
    result.validatedScripts = resolved;
    result.source = {
      type: best.source,
      moduleId,
      endpointId: best.endpointId,
      caseId: best.caseId || null,
      caseName: best.caseName || null,
      scenarioId: best.scenarioId || null,
      scenarioName: best.scenarioName || null,
      stepName: best.stepName || null,
      reasons: best.reasons,
      projectId: Number(project),
    };
    result.confidence = best.confidence;
    // Same module + same endpoint / target scenario can be high confidence; other same-module sources should still be confirmed
    result.requiresConfirmation = !['high'].includes(best.confidence);
  }
} else {
  result.warnings.push({
    fatal: true,
    message:
      'No verifiable auth pre-processor found for the current project + module. Do not patch one together from script-library keywords or script IDs of other projects/modules. Specify a same-module historical step manually.',
  });
}

const outPath =
  process.env.APIFOX_AUTH_OUT ||
  path.join(process.env.TEMP || '.', `apifox-auth-discovery-${endpointId}.json`);
writeJson(outPath, result);

console.log(
  JSON.stringify(
    {
      outPath,
      projectId: Number(project),
      moduleId,
      source: result.source,
      confidence: result.confidence,
      requiresConfirmation: result.requiresConfirmation,
      validatedScripts: result.validatedScripts,
      candidateCount: result.candidates.length,
      scenarioAuthHttpStepGroups: result.scenarioAuthHttpSteps.length,
      warningCount: result.warnings.length,
      policy: result.policy,
    },
    null,
    2
  )
);

if (!result.authPreProcessors) {
  console.warn('No verifiable auth pre-processor found for "current project + same module"; cross-module or hard-coded script IDs are forbidden.');
  process.exitCode = 2;
}
