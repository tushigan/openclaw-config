"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports._ = resolveOAuthApiKeyMarker;exports.a = void 0;exports.b = resolveProviderEnvAuthEvidence;exports.c = isAwsSdkAuthMarker;exports.d = isOAuthApiKeyMarker;exports.f = isSecretRefHeaderValueMarker;exports.g = resolveNonEnvSecretRefHeaderValueMarker;exports.h = resolveNonEnvSecretRefApiKeyMarker;exports.i = void 0;exports.l = isKnownEnvApiKeyMarker;exports.m = resolveEnvSecretRefHeaderValueMarker;exports.o = exports.n = void 0;exports.p = listKnownNonSecretApiKeyMarkers;exports.t = exports.s = exports.r = void 0;exports.u = isNonSecretApiKeyMarker;exports.v = listProviderEnvAuthLookupKeys;exports.y = resolveProviderEnvApiKeyCandidates;var _providerEnvVarsPk6C_sd = require("./provider-env-vars-pk6C_sd4.js");
var _manifestMetadataScanDS6GxP9a = require("./manifest-metadata-scan-DS6GxP9a.js");
//#region src/agents/model-auth-env-vars.ts
function resolveProviderEnvApiKeyCandidates(params) {
  return (0, _providerEnvVarsPk6C_sd.a)(params);
}
function resolveProviderEnvAuthEvidence(params) {
  return (0, _providerEnvVarsPk6C_sd.o)(params);
}
function listProviderEnvAuthLookupKeys(params) {
  return Array.from(new Set([...Object.keys(params.envCandidateMap), ...Object.keys(params.authEvidenceMap)])).toSorted((a, b) => a.localeCompare(b));
}
resolveProviderEnvApiKeyCandidates();
function listKnownProviderEnvApiKeyNames() {
  return (0, _providerEnvVarsPk6C_sd.n)();
}
//#endregion
//#region src/agents/model-auth-markers.ts
const MINIMAX_OAUTH_MARKER = exports.r = "minimax-oauth";
const OAUTH_API_KEY_MARKER_PREFIX = exports.a = "oauth:";
const OLLAMA_LOCAL_AUTH_MARKER = exports.o = "ollama-local";
const CUSTOM_LOCAL_AUTH_MARKER = exports.t = "custom-local";
const GCP_VERTEX_CREDENTIALS_MARKER = exports.n = "gcp-vertex-credentials";
const NON_ENV_SECRETREF_MARKER = exports.i = "secretref-managed";
const SECRETREF_ENV_HEADER_MARKER_PREFIX = exports.s = "secretref-env:";
const AWS_SDK_ENV_MARKERS = new Set([
"AWS_BEARER_TOKEN_BEDROCK",
"AWS_ACCESS_KEY_ID",
"AWS_PROFILE"]
);
const CORE_NON_SECRET_API_KEY_MARKERS = [
CUSTOM_LOCAL_AUTH_MARKER,
OLLAMA_LOCAL_AUTH_MARKER,
NON_ENV_SECRETREF_MARKER];

let knownEnvApiKeyMarkersCache;
let knownNonSecretApiKeyMarkersCache;
const LEGACY_ENV_API_KEY_MARKERS = [
"GOOGLE_API_KEY",
"DEEPSEEK_API_KEY",
"PERPLEXITY_API_KEY",
"FIREWORKS_API_KEY",
"NOVITA_API_KEY",
"AZURE_OPENAI_API_KEY",
"AZURE_API_KEY",
"MINIMAX_CODE_PLAN_KEY"];

function normalizeStringList(value) {
  if (!Array.isArray(value)) return [];
  return value.map((entry) => typeof entry === "string" ? entry.trim() : "").filter(Boolean);
}
function listKnownEnvApiKeyMarkers() {
  knownEnvApiKeyMarkersCache ??= new Set([
  ...listKnownProviderEnvApiKeyNames(),
  ...LEGACY_ENV_API_KEY_MARKERS,
  ...AWS_SDK_ENV_MARKERS]
  );
  return knownEnvApiKeyMarkersCache;
}
function listKnownNonSecretApiKeyMarkers() {
  knownNonSecretApiKeyMarkersCache ??= [...new Set([...CORE_NON_SECRET_API_KEY_MARKERS, ...(0, _manifestMetadataScanDS6GxP9a.t)().flatMap((plugin) => plugin.origin === "bundled" ? normalizeStringList(plugin.manifest.nonSecretAuthMarkers) : [])])];
  return [...knownNonSecretApiKeyMarkersCache];
}
function isAwsSdkAuthMarker(value) {
  return AWS_SDK_ENV_MARKERS.has(value.trim());
}
function isKnownEnvApiKeyMarker(value) {
  const trimmed = value.trim();
  return listKnownEnvApiKeyMarkers().has(trimmed) && !isAwsSdkAuthMarker(trimmed);
}
function resolveOAuthApiKeyMarker(providerId) {
  return `${OAUTH_API_KEY_MARKER_PREFIX}${providerId.trim()}`;
}
function isOAuthApiKeyMarker(value) {
  return value.trim().startsWith(OAUTH_API_KEY_MARKER_PREFIX);
}
function resolveNonEnvSecretRefApiKeyMarker(_source) {
  return NON_ENV_SECRETREF_MARKER;
}
function resolveNonEnvSecretRefHeaderValueMarker(_source) {
  return NON_ENV_SECRETREF_MARKER;
}
function resolveEnvSecretRefHeaderValueMarker(envVarName) {
  return `${SECRETREF_ENV_HEADER_MARKER_PREFIX}${envVarName.trim()}`;
}
function isSecretRefHeaderValueMarker(value) {
  const trimmed = value.trim();
  return trimmed === "secretref-managed" || trimmed.startsWith("secretref-env:");
}
function isNonSecretApiKeyMarker(value, opts) {
  const trimmed = value.trim();
  if (!trimmed) return false;
  if (isOAuthApiKeyMarker(trimmed) || listKnownNonSecretApiKeyMarkers().includes(trimmed) || isAwsSdkAuthMarker(trimmed)) return true;
  if (opts?.includeEnvVarName === false) return false;
  return listKnownEnvApiKeyMarkers().has(trimmed);
}
//#endregion /* v9-a8a597c268a0e64d */
