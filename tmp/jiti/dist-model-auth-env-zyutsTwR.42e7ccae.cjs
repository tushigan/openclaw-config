"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = resolveEnvApiKey;var _providerIdDIRgKpoh = require("./provider-id-DIRgKpoh.js");
var _ioE69J4lLI = require("./io-E69J4lLI.js");
var _providerAuthAliasesChhMyI_u = require("./provider-auth-aliases-ChhMyI_u.js");
var _setupRegistryDSA33nXk = require("./setup-registry-DSA33nXk.js");
var _modelAuthMarkersDBkfxh3_ = require("./model-auth-markers-DBkfxh3_.js");
var _normalizeSecretInputG30DI_5w = require("./normalize-secret-input-G30DI_5w.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodeOs = _interopRequireDefault(require("node:os"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/agents/model-auth-env.ts
function expandAuthEvidencePath(rawPath, env) {
  const trimmed = rawPath.trim();
  if (!trimmed) return;
  const homeDir = normalizeOptionalPathInput(env.HOME) ?? _nodeOs.default.homedir();
  const appDataDir = normalizeOptionalPathInput(env.APPDATA);
  if (trimmed.includes("${APPDATA}") && !appDataDir) return;
  return trimmed.replaceAll("${HOME}", homeDir).replaceAll("${APPDATA}", appDataDir ?? "");
}
function normalizeOptionalPathInput(value) {
  if (typeof value !== "string") return;
  const trimmed = value.trim();
  return trimmed ? trimmed : void 0;
}
function hasRequiredAuthEvidenceEnv(evidence, env) {
  const hasEnv = (key) => Boolean((0, _normalizeSecretInputG30DI_5w.t)(env[key]));
  if (evidence.requiresAnyEnv?.length && !evidence.requiresAnyEnv.some(hasEnv)) return false;
  if (evidence.requiresAllEnv?.length && !evidence.requiresAllEnv.every(hasEnv)) return false;
  return true;
}
function hasLocalFileAuthEvidence(evidence, env) {
  if (evidence.fileEnvVar) {
    const explicitPath = normalizeOptionalPathInput(env[evidence.fileEnvVar]);
    if (explicitPath) return _nodeFs.default.existsSync(explicitPath);
  }
  for (const rawPath of evidence.fallbackPaths ?? []) {
    const expandedPath = expandAuthEvidencePath(rawPath, env);
    if (expandedPath && _nodeFs.default.existsSync(expandedPath)) return true;
  }
  return false;
}
function resolveAuthEvidence(evidence, env) {
  for (const entry of evidence ?? []) {
    if (entry.type !== "local-file-with-env") continue;
    if (!hasRequiredAuthEvidenceEnv(entry, env) || !hasLocalFileAuthEvidence(entry, env)) continue;
    return {
      apiKey: entry.credentialMarker,
      source: entry.source ?? "local auth evidence"
    };
  }
  return null;
}
function resolveEnvApiKey(provider, env = process.env, options = {}) {
  const normalizedProvider = (0, _providerIdDIRgKpoh.i)(provider);
  const lookupParams = {
    config: options.config,
    workspaceDir: options.workspaceDir,
    env
  };
  const normalized = options.aliasMap ? options.aliasMap[normalizedProvider] ?? normalizedProvider : (0, _providerAuthAliasesChhMyI_u.r)(provider, lookupParams);
  const candidateMap = options.candidateMap ?? (0, _modelAuthMarkersDBkfxh3_.y)(lookupParams);
  const authEvidenceMap = options.authEvidenceMap ?? (0, _modelAuthMarkersDBkfxh3_.b)(lookupParams);
  const applied = new Set((0, _ioE69J4lLI.G)());
  const pick = (envVar) => {
    const value = (0, _normalizeSecretInputG30DI_5w.t)(env[envVar]);
    if (!value) return null;
    return {
      apiKey: value,
      source: applied.has(envVar) ? `shell env: ${envVar}` : `env: ${envVar}`
    };
  };
  const candidates = Object.hasOwn(candidateMap, normalized) ? candidateMap[normalized] : void 0;
  if (Array.isArray(candidates)) for (const envVar of candidates) {
    const resolved = pick(envVar);
    if (resolved) return resolved;
  }
  const authEvidence = resolveAuthEvidence(Object.hasOwn(authEvidenceMap, normalized) ? authEvidenceMap[normalized] : void 0, env);
  if (authEvidence) return authEvidence;
  if (Array.isArray(candidates)) return null;
  const setupProvider = (0, _setupRegistryDSA33nXk.i)({
    provider: normalized,
    env
  });
  if (setupProvider?.resolveConfigApiKey) {
    const resolved = setupProvider.resolveConfigApiKey({
      provider: normalized,
      env
    });
    if (resolved?.trim()) return {
      apiKey: resolved,
      source: resolved === "gcp-vertex-credentials" ? "gcloud adc" : "env"
    };
  }
  return null;
}
//#endregion /* v9-378b41270c1cb75e */
