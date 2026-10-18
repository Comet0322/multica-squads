/**
 * Apifox supplementary test case JSON generator.
 * The number of cases is determined entirely by caseSpecs; there is no fixed list; evidence, probe results and expectations are all strictly validated.
 */
const fs = require('fs');
const path = require('path');

const skillDir = __dirname;
const configArgIndex = process.argv.indexOf('--config');
const userConfigPath =
  configArgIndex >= 0 && process.argv[configArgIndex + 1]
    ? path.resolve(process.argv[configArgIndex + 1])
    : path.join(skillDir, 'config.json');

function loadConfig() {
  if (!fs.existsSync(userConfigPath)) {
    console.error(
      `Not found: ${userConfigPath}\n` +
        'Copy config.example.json to config.json and rewrite caseSpecs for the current endpoint (the count depends on the endpoint; do not copy the example).'
    );
    process.exit(1);
  }

  const fileConfig = JSON.parse(fs.readFileSync(userConfigPath, 'utf8'));

  const successResponseId =
    fileConfig.successResponseId ||
    fileConfig.endpoint?.responseId ||
    process.env.APIFOX_SUCCESS_RESPONSE_ID;

  return {
    fileConfig,
    apiDetailId: Number(process.env.APIFOX_ENDPOINT_ID || fileConfig.APIFOX_ENDPOINT_ID),
    method: fileConfig.endpoint?.method || 'post',
    apiPath: fileConfig.endpoint?.path,
    authPreProcessors: fileConfig.authPreProcessors || null,
    authDiscovery: fileConfig.authDiscovery,
    categories: fileConfig.categoryIds || { positive: 211, negative: 212, boundary: 213 },
    baseRequest: fileConfig.baseRequest || {},
    defaultSuccessResponseId: successResponseId,
    caseSpecs: fileConfig.caseSpecs,
    targetEnvironment: fileConfig.targetEnvironment,
    namePrefix: process.env.APIFOX_CASE_NAME_PREFIX || fileConfig.namePrefix || 'endpoint',
    outputDir:
      process.env.APIFOX_CASE_OUTPUT_DIR ||
      path.join(process.env.TEMP || '/tmp', `apifox-cases-${process.env.APIFOX_ENDPOINT_ID || 'custom'}`),
  };
}

const cfg = loadConfig();

function die(message) {
  console.error(`Config error: ${message}`);
  process.exit(1);
}

function nonEmpty(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function findSecret(value, trail = '') {
  if (!value || typeof value !== 'object') return null;
  for (const [key, child] of Object.entries(value)) {
    const here = trail ? `${trail}.${key}` : key;
    if (/access.?token|api.?token/i.test(key)) return here;
    if (typeof child === 'string' && /^afpp_/i.test(child)) return here;
    const nested = findSecret(child, here);
    if (nested) return nested;
  }
  return null;
}

const secretPath = findSecret(JSON.parse(fs.readFileSync(userConfigPath, 'utf8')));
if (secretPath) die(`${secretPath} appears to contain a token; the token must only be provided via the APIFOX_ACCESS_TOKEN environment variable`);
const projectIdRaw = String(cfg.fileConfig.APIFOX_PROJECT_ID || process.env.APIFOX_PROJECT_ID || '');
if (!projectIdRaw || /REPLACE_/i.test(projectIdRaw)) {
  die('APIFOX_PROJECT_ID is not set or is still a placeholder; do not copy config.example.json as-is');
}
if (!cfg.apiDetailId || !cfg.apiPath) die('Missing APIFOX_ENDPOINT_ID or endpoint.path');
if (/REPLACE_/i.test(String(cfg.apiPath)) || /REPLACE_/i.test(String(cfg.apiDetailId))) {
  die('endpoint is still a placeholder; fill in the real method/path/ID for the current task');
}
if (/REPLACE_/i.test(String(cfg.targetEnvironment.id || '')) || /REPLACE_/i.test(String(cfg.targetEnvironment.name || ''))) {
  die('targetEnvironment is still a placeholder; the environment ID/name must belong to the currently confirmed project');
}
if (!/^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$/i.test(cfg.method)) die(`Unsupported method: ${cfg.method}`);
if (!cfg.targetEnvironment || cfg.targetEnvironment.type !== 'non-production') {
  die('targetEnvironment.type must be explicitly non-production; probing against production is forbidden by default');
}
if (!nonEmpty(String(cfg.targetEnvironment.id || ''))) die('targetEnvironment.id is required');
if (!Array.isArray(cfg.caseSpecs) || cfg.caseSpecs.length === 0) {
  die('caseSpecs must be a non-empty array; the count is decided by scenario evidence, do not copy the example');
}
if (!Array.isArray(cfg.authPreProcessors) || !cfg.authPreProcessors.length) {
  die('authPreProcessors must not be empty; run discover-auth.js first and manually confirm the discovery result');
}
if (!cfg.authDiscovery || !nonEmpty(cfg.authDiscovery.source) || !nonEmpty(cfg.authDiscovery.confidence)) {
  die('authDiscovery.source/confidence are required, to trace the auth origin');
}
if (!nonEmpty(String(cfg.authDiscovery.moduleId || '')) || !nonEmpty(String(cfg.authDiscovery.projectId || ''))) {
  die('authDiscovery.moduleId/projectId are required: auth must state which project + module it comes from; cross-module reuse is forbidden');
}
if (String(cfg.authDiscovery.projectId) !== String(cfg.fileConfig?.APIFOX_PROJECT_ID || process.env.APIFOX_PROJECT_ID || '')) {
  die('authDiscovery.projectId must match the current APIFOX_PROJECT_ID');
}
if (!['high', 'medium', 'low'].includes(cfg.authDiscovery.confidence)) {
  die('authDiscovery.confidence must be high | medium | low');
}
if (cfg.authDiscovery.confidence !== 'high' && cfg.authDiscovery.confirmed !== true) {
  die('A non-high confidence auth result must set authDiscovery.confirmed=true, meaning it was manually confirmed');
}
if (!Array.isArray(cfg.authDiscovery.validatedScripts) || !cfg.authDiscovery.validatedScripts.length) {
  die('authDiscovery.validatedScripts is required: list the script id/name already validated against common-script in the current project');
}
for (const script of cfg.authDiscovery.validatedScripts) {
  if (!nonEmpty(String(script.id || '')) || /REPLACE_/i.test(String(script.id))) {
    die('validatedScripts contains a placeholder or empty id: run discover-auth.js for the current module first; do not copy the example');
  }
  if (!nonEmpty(String(script.name || '')) || /REPLACE_/i.test(String(script.name))) {
    die('validatedScripts.name must not be empty or a placeholder');
  }
}
for (const processor of cfg.authPreProcessors) {
  if (processor?.type !== 'commonScript' || !Array.isArray(processor.data)) continue;
  for (const id of processor.data) {
    if (/REPLACE_/i.test(String(id))) {
      die('authPreProcessors contains a placeholder script ID: it must be copied verbatim from a historical step in the same module');
    }
    const hit = cfg.authDiscovery.validatedScripts.find(
      (script) => String(script.id) === String(id) && nonEmpty(String(script.name || ''))
    );
    if (!hit) {
      die(
        `authPreProcessors contains unvalidated or unknown script ID ${id}. Cross-project/cross-module reuse is forbidden; copy verbatim from a sibling step in the same module via with-case-detail`
      );
    }
  }
}

function assertion(name, subject, comparison, value, jsonPath = '') {
  // The Apifox UI echoes the JSONPath from extractSettings.expression; it must equal path (compare with a hand-written case)
  const extractSettings = {
    expression: jsonPath || '',
    continueExtractorSettings: { isContinueExtractValue: false },
  };
  return {
    type: 'assertion',
    data: { name, subject, comparison, value: String(value), path: jsonPath, extractSettings },
    defaultEnable: true,
    enable: true,
  };
}

function deepClone(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function deepMerge(base, patch) {
  if (Array.isArray(patch)) return deepClone(patch);
  if (!patch || typeof patch !== 'object') return patch;
  const out = base && typeof base === 'object' && !Array.isArray(base) ? deepClone(base) : {};
  for (const [key, value] of Object.entries(patch)) {
    out[key] =
      value && typeof value === 'object' && !Array.isArray(value)
        ? deepMerge(out[key], value)
        : deepClone(value);
  }
  return out;
}

function splitPath(dotPath) {
  return String(dotPath).split('.').filter(Boolean);
}

function setByPath(obj, dotPath, value) {
  const parts = splitPath(dotPath);
  if (!parts.length) die(`Invalid override path: ${dotPath}`);
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i += 1) {
    if (!cur[parts[i]] || typeof cur[parts[i]] !== 'object') cur[parts[i]] = {};
    cur = cur[parts[i]];
  }
  cur[parts.at(-1)] = deepClone(value);
}

function deleteByPath(obj, dotPath) {
  const parts = splitPath(dotPath);
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i += 1) {
    if (!cur || typeof cur !== 'object') return;
    cur = cur[parts[i]];
  }
  if (cur && typeof cur === 'object') delete cur[parts.at(-1)];
}

function normalizeRequest(spec) {
  const req = deepMerge(cfg.baseRequest, spec.request || {});
  if (spec.bodyTransform) {
    const body = deepClone(req.requestBody?.data);
    if (!body || typeof body !== 'object' || Array.isArray(body)) {
      die(`${spec.nameSuffix}: bodyTransform only applies to object-type JSON requestBody.data`);
    }
    for (const key of spec.bodyTransform.omit || []) deleteByPath(body, key);
    for (const [key, value] of Object.entries(spec.bodyTransform.override || {})) setByPath(body, key, value);
    req.requestBody = { ...(req.requestBody || {}), data: body };
  }
  req.parameters ||= { path: [], query: [], header: [], cookie: [] };
  req.commonParameters ||= {};
  if (req.requestBody && typeof req.requestBody.data !== 'string') {
    const type = String(req.requestBody.type || '');
    if (type.includes('json')) req.requestBody.data = JSON.stringify(req.requestBody.data);
  }
  return req;
}

function validateEvidence(spec, index) {
  const evidence = spec.evidence;
  if (!evidence || typeof evidence !== 'object') die(`caseSpecs[${index}].evidence must be an object`);
  if (!evidence.scenario || typeof evidence.scenario !== 'object') {
    die(`${spec.nameSuffix}: evidence.scenario is required`);
  }
  const allowed = ['api-definition', 'requirement', 'existing-case', 'probe', 'combined'];
  if (!allowed.includes(evidence.scenario.type)) {
    die(`${spec.nameSuffix}: evidence.scenario.type must be ${allowed.join(' | ')}`);
  }
  if (!nonEmpty(evidence.scenario.source) || !nonEmpty(evidence.scenario.summary)) {
    die(`${spec.nameSuffix}: evidence.scenario.source/summary are required and must not be empty`);
  }
  const probe = evidence.probe;
  if (!probe || typeof probe !== 'object') die(`${spec.nameSuffix}: evidence.probe is required`);
  for (const field of ['environmentId', 'observedAt', 'responseSummary']) {
    if (!nonEmpty(String(probe[field] || ''))) die(`${spec.nameSuffix}: evidence.probe.${field} is required`);
  }
  if (String(probe.environmentId) !== String(cfg.targetEnvironment.id)) {
    die(`${spec.nameSuffix}: probe.environmentId must match targetEnvironment.id`);
  }
  if (!Number.isInteger(Number(probe.statusCode))) die(`${spec.nameSuffix}: probe.statusCode must be an integer`);
}

function resolveCategoryId(spec) {
  if (typeof spec.categoryId === 'number') return spec.categoryId;
  if (typeof spec.category === 'number') return spec.category;
  const key = String(spec.category || 'positive');
  const id = cfg.categories[key];
  if (!id) {
    die(`Unknown category: ${key}; configure categoryIds.${key} or set categoryId directly`);
  }
  return id;
}

function buildAssertions(spec) {
  const expected = spec.expected;
  const status = String(expected.statusCode);
  const list = [assertion(`HTTP status ${status}`, 'httpCode', 'equal', status)];
  for (const [jsonPath, value] of Object.entries(expected.hardEquals || {})) {
    list.push(assertion(`${jsonPath}=${value}`, 'responseJson', 'equal', value, jsonPath));
  }
  for (const jsonPath of expected.exists || []) {
    list.push(assertion(`${jsonPath} exists`, 'responseJson', 'exists', '', jsonPath));
  }
  for (const [jsonPath, value] of Object.entries(expected.includes || {})) {
    list.push(assertion(`${jsonPath} includes ${value}`, 'responseJson', 'include', value, jsonPath));
  }
  for (const jsonPath of expected.notExists || []) {
    list.push(assertion(`${jsonPath} does not exist`, 'responseJson', 'notExist', '', jsonPath));
  }
  return list;
}

function validateExpected(spec) {
  const expected = spec.expected;
  if (!expected || typeof expected !== 'object') die(`${spec.nameSuffix}: expected is required`);
  if (!Number.isInteger(Number(expected.statusCode))) die(`${spec.nameSuffix}: expected.statusCode must be an integer`);
  if (Number(expected.statusCode) !== Number(spec.evidence.probe.statusCode)) {
    die(`${spec.nameSuffix}: expected.statusCode does not match the probed probe.statusCode (mismatch)`);
  }
  if (typeof expected.responseValidate !== 'boolean') {
    die(`${spec.nameSuffix}: expected.responseValidate must be explicitly true/false`);
  }
  if (expected.responseValidate && !(expected.responseId || cfg.defaultSuccessResponseId)) {
    die(`${spec.nameSuffix}: when response validation is enabled, expected.responseId or successResponseId must be provided`);
  }
  if (!expected.responseValidate && expected.responseId && Number(expected.responseId) !== 0) {
    die(`${spec.nameSuffix}: when response validation is disabled, responseId must be 0 or omitted`);
  }
  const jsonPaths = [
    ...Object.keys(expected.hardEquals || {}),
    ...(expected.exists || []),
    ...Object.keys(expected.includes || {}),
    ...(expected.notExists || []),
  ];
  for (const jsonPath of jsonPaths) {
    if (!nonEmpty(jsonPath) || !jsonPath.startsWith('$')) {
      die(`${spec.nameSuffix}: response assertion path must be a JSONPath (starting with $): ${jsonPath}`);
    }
  }
}

function validateSideEffect(spec) {
  const sideEffect = spec.sideEffect;
  if (!sideEffect || typeof sideEffect !== 'object') die(`${spec.nameSuffix}: sideEffect is required`);
  if (!['none', 'read', 'write', 'destructive'].includes(sideEffect.level)) {
    die(`${spec.nameSuffix}: sideEffect.level must be none | read | write | destructive`);
  }
  if (!nonEmpty(sideEffect.testData) || !nonEmpty(sideEffect.cleanup)) {
    die(`${spec.nameSuffix}: sideEffect.testData/cleanup are required`);
  }
}

function mkCase(spec) {
  const req = normalizeRequest(spec);
  const expected = spec.expected;
  const responseId = expected.responseValidate
    ? expected.responseId || cfg.defaultSuccessResponseId
    : 0;
  return {
    name: `${cfg.namePrefix}-${spec.nameSuffix}`,
    categoryId: resolveCategoryId(spec),
    apiDetailId: cfg.apiDetailId,
    method: cfg.method,
    path: cfg.apiPath,
    responseId,
    parameters: req.parameters,
    commonParameters: req.commonParameters,
    ...(req.requestBody ? { requestBody: req.requestBody } : {}),
    preProcessors: spec.preProcessors !== undefined ? spec.preProcessors : cfg.authPreProcessors,
    postProcessors: [
      ...buildAssertions(spec),
      ...(Array.isArray(spec.postProcessors) ? spec.postProcessors : []),
    ],
    auth: req.auth || {},
    options: { ...(req.options || {}), responseValidate: expected.responseValidate },
    advancedSettings: req.advancedSettings || { disabledSystemHeaders: {} },
  };
}

const evidenceLines = [];
const names = new Set();
const files = new Set();
const prepared = [];
for (const [index, spec] of cfg.caseSpecs.entries()) {
  if (!nonEmpty(spec.nameSuffix)) die(`caseSpecs[${index}].nameSuffix is required`);
  if (/\u672a\u9274\u6743|\u672a\u767b\u5f55|unauth|no[-_ ]?auth/i /* \u672a\u9274\u6743 = "unauthenticated", \u672a\u767b\u5f55 = "not logged in" (Chinese spec text is still matched) */.test(`${spec.nameSuffix} ${JSON.stringify(spec.evidence || {})}`)) {
    die(`${spec.nameSuffix}: this skill must not generate unauthenticated scenarios`);
  }
  validateEvidence(spec, index);
  validateExpected(spec);
  validateSideEffect(spec);
  const fullName = `${cfg.namePrefix}-${spec.nameSuffix}`;
  if (names.has(fullName)) die(`Duplicate case name: ${fullName}`);
  names.add(fullName);
  const file = spec.file || `${String(index + 1).padStart(2, '0')}-${spec.nameSuffix.replace(/[^\w\u4e00-\u9fff-]+/g, '_')}.json`;
  if (path.basename(file) !== file || !file.toLowerCase().endsWith('.json')) die(`${spec.nameSuffix}: file must be a .json file name in the current directory`);
  if (files.has(file.toLowerCase())) die(`Duplicate file name: ${file}`);
  files.add(file.toLowerCase());
  prepared.push({ file, caseObject: mkCase(spec) });
  evidenceLines.push(
    `- ${fullName} | ${spec.evidence.scenario.type}: ${spec.evidence.scenario.source} | ` +
      `${spec.evidence.scenario.summary} | probe=${spec.evidence.probe.environmentId}@${spec.evidence.probe.observedAt}`
  );
}

if (process.argv.includes('--validate-only')) {
  console.log(`config valid: ${prepared.length} cases`);
  process.exit(0);
}

fs.mkdirSync(cfg.outputDir, { recursive: true });
for (const item of prepared) {
  fs.writeFileSync(path.join(cfg.outputDir, item.file), JSON.stringify(item.caseObject, null, 2), 'utf8');
}

fs.writeFileSync(
  path.join(cfg.outputDir, 'checklist.md'),
  `# Pre-merge self-check\n\n` +
    `- [x] Count=${cfg.caseSpecs.length}, all from caseSpecs (not a fixed template)\n` +
    `- [x] Every evidence and probe passed structural validation\n` +
    `- [ ] path is non-empty; auth comes from same-module discovery\n` +
    `- [ ] Negative cases: responseId=0 + responseValidate=false\n` +
    `- [ ] Positive cases bind the success response; assertions calibrated against probe results\n` +
    `- [ ] No unauthenticated cases generated\n\n` +
    `## Cases and evidence in this batch\n\n${evidenceLines.join('\n')}\n`
);

console.log(`written ${cfg.caseSpecs.length} cases to ${cfg.outputDir}`);
