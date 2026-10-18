/**
 * System <-> project registry (persisted locally / in the workspace; contains no token).
 *
 * Path resolution (in priority order):
 *   1) APIFOX_SYSTEMS_REGISTRY —— full file path (Multica can point it at a workspace-level file)
 *   2) APIFOX_SKILL_STATE_DIR/systems-registry[.operator].json
 *   3) <skill>/.apifox/systems-registry[.operator].json
 * operator comes from APIFOX_OPERATOR or APIFOX_USER_EMAIL (isolates the registry when several people share one Skill directory)
 *
 * Usage:
 *   node systems-registry.js path
 *   node systems-registry.js list
 *   node systems-registry.js lookup --name "SomeSystem"
 *   node systems-registry.js upsert --name "NewSystem" --project-id 123 --project-name "NewSystem" [--env-id 456 --env-name test --ai-branch ai/...]
 *
 * Rules:
 * - After the user supplies a projectId and it passes project get validation, it must be upserted
 * - lookup uses exact matching only (equal after normalize); fuzzy hits are forbidden
 * - A liveness check via project get / environment get is still required
 */
const fs = require('fs');
const path = require('path');

const skillRoot = path.join(__dirname, '..');
const defaultApifoxDir = path.join(skillRoot, '.apifox');

function normalize(name) {
  return String(name || '')
    .trim()
    .toLowerCase()
    .replace(/[\s_\-]+/g, '')
    // full-width parentheses are normalized to ASCII
    .replace(/\uff08/g, '(')
    .replace(/\uff09/g, ')');
}

function operatorSuffix() {
  const raw = process.env.APIFOX_OPERATOR || process.env.APIFOX_USER_EMAIL || '';
  const key = normalize(raw).replace(/[^a-z0-9\u4e00-\u9fff]/gi, '');
  return key ? `.${key}` : '';
}

function resolveRegistryPath() {
  if (process.env.APIFOX_SYSTEMS_REGISTRY) {
    return path.resolve(process.env.APIFOX_SYSTEMS_REGISTRY);
  }
  const stateDir = process.env.APIFOX_SKILL_STATE_DIR
    ? path.resolve(process.env.APIFOX_SKILL_STATE_DIR)
    : defaultApifoxDir;
  return path.join(stateDir, `systems-registry${operatorSuffix()}.json`);
}

function emptyRegistry() {
  return {
    version: 1,
    updatedAt: new Date().toISOString(),
    systems: {},
    _comment: 'Dynamic registry; contains no token. Do not ship a personal registry in the shared Skill distribution.',
  };
}

function load() {
  const registryPath = resolveRegistryPath();
  if (!fs.existsSync(registryPath)) {
    return emptyRegistry();
  }
  const data = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
  if (!data.systems || typeof data.systems !== 'object') data.systems = {};
  return data;
}

function save(data) {
  const registryPath = resolveRegistryPath();
  data.updatedAt = new Date().toISOString();
  fs.mkdirSync(path.dirname(registryPath), { recursive: true });
  fs.writeFileSync(registryPath, JSON.stringify(data, null, 2) + '\n', 'utf8');
  return registryPath;
}

function arg(name, def = '') {
  const i = process.argv.indexOf(name);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  return def;
}

function findSystem(data, name) {
  const key = normalize(name);
  if (!key) return null;
  if (data.systems[key]) return data.systems[key];
  for (const item of Object.values(data.systems)) {
    const names = [item.systemKey, item.displayName, ...(item.aliases || [])].map(normalize);
    if (names.includes(key)) return item;
  }
  return null;
}

function cmdPath() {
  console.log(
    JSON.stringify(
      {
        registryPath: resolveRegistryPath(),
        exists: fs.existsSync(resolveRegistryPath()),
        via: process.env.APIFOX_SYSTEMS_REGISTRY
          ? 'APIFOX_SYSTEMS_REGISTRY'
          : process.env.APIFOX_SKILL_STATE_DIR
            ? 'APIFOX_SKILL_STATE_DIR'
            : 'skill/.apifox',
        operator: process.env.APIFOX_OPERATOR || process.env.APIFOX_USER_EMAIL || null,
      },
      null,
      2
    )
  );
}

function cmdList() {
  const registryPath = resolveRegistryPath();
  const data = load();
  const rows = Object.values(data.systems).map((item) => ({
    displayName: item.displayName,
    projectId: item.projectId,
    projectName: item.projectName,
    environmentId: item.environmentId || null,
    environmentName: item.environmentName || null,
    aiBranch: item.aiBranch || null,
    aliases: item.aliases || [],
    updatedAt: item.updatedAt,
    updatedBy: item.updatedBy || null,
  }));
  console.log(JSON.stringify({ registryPath, count: rows.length, systems: rows }, null, 2));
}

function cmdLookup() {
  const name = arg('--name');
  if (!name) {
    console.error('Usage: node systems-registry.js lookup --name <system-name>');
    process.exit(1);
  }
  const registryPath = resolveRegistryPath();
  const hit = findSystem(load(), name);
  if (!hit) {
    console.log(JSON.stringify({ found: false, name, registryPath }, null, 2));
    process.exitCode = 2;
    return;
  }
  console.log(JSON.stringify({ found: true, system: hit, registryPath }, null, 2));
}

function cmdUpsert() {
  const name = arg('--name');
  const projectId = arg('--project-id');
  const projectName = arg('--project-name', name);
  const envId = arg('--env-id', '');
  const envName = arg('--env-name', '');
  const sourceBranch = arg('--source-branch', 'main');
  const aiBranch = arg('--ai-branch', '');
  const aliasRaw = arg('--aliases', '');
  const notes = arg('--notes', '');

  if (!name || !projectId) {
    console.error(
      'Usage: node systems-registry.js upsert --name <system-name> --project-id <id> [--project-name <name>] [--env-id <id>] [--env-name <name>] [--ai-branch <branch>] [--aliases a,b]'
    );
    process.exit(1);
  }
  if (!/^\d+$/.test(String(projectId))) {
    console.error('project-id must be a number');
    process.exit(1);
  }

  const data = load();
  const key = normalize(name);
  const existing = findSystem(data, name) || {};
  const aliases = Array.from(
    new Set([
      ...(existing.aliases || []),
      name,
      projectName,
      ...aliasRaw
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    ])
  );

  const record = {
    systemKey: key,
    displayName: projectName || name,
    aliases,
    projectId: String(projectId),
    projectName: projectName || name,
    environmentId: envId ? String(envId) : existing.environmentId || null,
    environmentName: envName || existing.environmentName || null,
    sourceBranch: sourceBranch || existing.sourceBranch || 'main',
    aiBranch: aiBranch || existing.aiBranch || null,
    notes: notes || existing.notes || '',
    updatedAt: new Date().toISOString(),
    updatedBy: process.env.APIFOX_OPERATOR || process.env.APIFOX_USER_EMAIL || 'agent',
  };

  if (existing.systemKey && existing.systemKey !== key && data.systems[existing.systemKey]) {
    delete data.systems[existing.systemKey];
  }
  data.systems[key] = record;
  const registryPath = save(data);
  console.log(JSON.stringify({ ok: true, registryPath, system: record }, null, 2));
}

const cmd = process.argv[2];
if (cmd === 'path') cmdPath();
else if (cmd === 'list') cmdList();
else if (cmd === 'lookup') cmdLookup();
else if (cmd === 'upsert') cmdUpsert();
else {
  console.error('Usage: node systems-registry.js <path|list|lookup|upsert> ...');
  process.exit(1);
}
