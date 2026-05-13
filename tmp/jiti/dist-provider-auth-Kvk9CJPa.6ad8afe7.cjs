"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = void 0;exports.c = isProviderApiKeyConfigured;exports.d = resolveCopilotApiToken;exports.f = resolveProviderAuthProfileApiKey;exports.h = toFormUrlEncoded;exports.i = void 0;exports.l = isProviderAuthProfileConfigured;exports.m = generatePkceVerifierChallenge;exports.n = void 0;exports.o = buildCopilotIdeHeaders;exports.p = generateHexPkceVerifierChallenge;exports.r = void 0;exports.s = deriveCopilotApiBaseUrlFromToken;exports.t = void 0;exports.u = listUsableProviderAuthProfileIds;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _pathsC1_Y0cDn = require("./paths-C1_Y0cDn.js");
require("./types.secrets-CL51SR4g.js");
var _jsonFileBDXsHiio = require("./json-file-BDXsHiio.js");
require("./ref-contract-FVeYRZYq.js");
require("./provider-env-vars-pk6C_sd4.js");
var _storeCSOk8Bno = require("./store-CSOk8Bno.js");
var _agentPathsUmbOEWUL = require("./agent-paths-umbOEWUL.js");
require("./model-auth-markers-DBkfxh3_.js");
var _modelAuthEnvZyutsTwR = require("./model-auth-env-zyutsTwR.js");
require("./models-config.providers.secrets-CnWymX4N.js");
var _providerAttributionDaSNL9Cf = require("./provider-attribution-DaSNL9Cf.js");
var _oauthDoxNzd = require("./oauth-DoxNzd4-.js");
var _profileListDRiyVI2U = require("./profile-list-DRiyVI2U.js");
require("./repair-BvCst034.js");
var _order7oO26mfB = require("./order-7oO26mfB.js");
require("./profiles-CjRHFJUw.js");
require("./provider-model-shared-DMDlhIax.js");
require("./provider-auth-input-DwYHjGoF.js");
require("./provider-auth-helpers-CvYCN4Y4.js");
require("./provider-api-key-auth-Fnbxn4uv.js");
var _nodePath = _interopRequireDefault(require("node:path"));
var _nodeCrypto = require("node:crypto");function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/plugin-sdk/oauth-utils.ts
/** Encode a flat object as application/x-www-form-urlencoded form data. */
function toFormUrlEncoded(data) {
  return Object.entries(data).map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`).join("&");
}
/** Generate a PKCE verifier/challenge pair suitable for OAuth authorization flows. */
function generatePkceVerifierChallenge() {
  const verifier = (0, _nodeCrypto.randomBytes)(32).toString("base64url");
  return {
    verifier,
    challenge: (0, _nodeCrypto.createHash)("sha256").update(verifier).digest("base64url")
  };
}
/** Generate a PKCE verifier/challenge pair with a 64-character hex verifier. */
function generateHexPkceVerifierChallenge() {
  const verifier = (0, _nodeCrypto.randomBytes)(32).toString("hex");
  return {
    verifier,
    challenge: (0, _nodeCrypto.createHash)("sha256").update(verifier).digest("base64url")
  };
}
//#endregion
//#region src/plugin-sdk/provider-auth.ts
const COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token";
const COPILOT_EDITOR_VERSION = exports.n = "vscode/1.96.2";
const COPILOT_USER_AGENT = exports.i = "GitHubCopilotChat/0.26.7";
const COPILOT_EDITOR_PLUGIN_VERSION = exports.t = "copilot-chat/0.35.0";
const COPILOT_GITHUB_API_VERSION = exports.r = "2025-04-01";
const DEFAULT_COPILOT_API_BASE_URL = exports.a = "https://api.individual.githubcopilot.com";
function buildCopilotIdeHeaders(params = {}) {
  return {
    "Editor-Version": COPILOT_EDITOR_VERSION,
    "Editor-Plugin-Version": COPILOT_EDITOR_PLUGIN_VERSION,
    "User-Agent": COPILOT_USER_AGENT,
    ...(params.includeApiVersion ? { "X-Github-Api-Version": COPILOT_GITHUB_API_VERSION } : {})
  };
}
function resolveCopilotTokenCachePath(env = process.env) {
  return _nodePath.default.join((0, _pathsC1_Y0cDn.v)(env), "credentials", "github-copilot.token.json");
}
function isCopilotTokenUsable(cache, now = Date.now()) {
  return cache.expiresAt - now > 300 * 1e3;
}
function parseCopilotTokenResponse(value) {
  if (!value || typeof value !== "object") throw new Error("Unexpected response from GitHub Copilot token endpoint");
  const asRecord = value;
  const token = asRecord.token;
  const expiresAt = asRecord.expires_at;
  if (typeof token !== "string" || token.trim().length === 0) throw new Error("Copilot token response missing token");
  let expiresAtMs;
  if (typeof expiresAt === "number" && Number.isFinite(expiresAt)) expiresAtMs = expiresAt < 1e11 ? expiresAt * 1e3 : expiresAt;else
  if (typeof expiresAt === "string" && expiresAt.trim().length > 0) {
    const parsed = Number.parseInt(expiresAt, 10);
    if (!Number.isFinite(parsed)) throw new Error("Copilot token response has invalid expires_at");
    expiresAtMs = parsed < 1e11 ? parsed * 1e3 : parsed;
  } else throw new Error("Copilot token response missing expires_at");
  return {
    token,
    expiresAt: expiresAtMs
  };
}
function resolveCopilotProxyHost(proxyEp) {
  const trimmed = proxyEp.trim();
  if (!trimmed) return null;
  const urlText = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
  try {
    const url = new URL(urlText);
    if (url.protocol !== "http:" && url.protocol !== "https:") return null;
    return (0, _stringCoerceBje8XVt.a)(url.hostname);
  } catch {
    return null;
  }
}
function deriveCopilotApiBaseUrlFromToken(token) {
  const trimmed = token.trim();
  if (!trimmed) return null;
  const proxyEp = trimmed.match(/(?:^|;)\s*proxy-ep=([^;\s]+)/i)?.[1]?.trim();
  if (!proxyEp) return null;
  const proxyHost = resolveCopilotProxyHost(proxyEp);
  if (!proxyHost) return null;
  const baseUrl = `https://${proxyHost.replace(/^proxy\./i, "api.")}`;
  return (0, _providerAttributionDaSNL9Cf.n)(baseUrl).endpointClass === "invalid" ? null : baseUrl;
}
async function resolveCopilotApiToken(params) {
  const env = params.env ?? process.env;
  const cachePath = params.cachePath?.trim() || resolveCopilotTokenCachePath(env);
  const loadJsonFileFn = params.loadJsonFileImpl ?? _jsonFileBDXsHiio.t;
  const saveJsonFileFn = params.saveJsonFileImpl ?? _jsonFileBDXsHiio.n;
  const cached = loadJsonFileFn(cachePath);
  if (cached && typeof cached.token === "string" && typeof cached.expiresAt === "number") {
    if (isCopilotTokenUsable(cached)) return {
      token: cached.token,
      expiresAt: cached.expiresAt,
      source: `cache:${cachePath}`,
      baseUrl: deriveCopilotApiBaseUrlFromToken(cached.token) ?? "https://api.individual.githubcopilot.com"
    };
  }
  const res = await (params.fetchImpl ?? fetch)(COPILOT_TOKEN_URL, {
    method: "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${params.githubToken}`,
      ...buildCopilotIdeHeaders({ includeApiVersion: true })
    }
  });
  if (!res.ok) throw new Error(`Copilot token exchange failed: HTTP ${res.status}`);
  const json = parseCopilotTokenResponse(await res.json());
  const payload = {
    token: json.token,
    expiresAt: json.expiresAt,
    updatedAt: Date.now()
  };
  saveJsonFileFn(cachePath, payload);
  return {
    token: payload.token,
    expiresAt: payload.expiresAt,
    source: `fetched:${COPILOT_TOKEN_URL}`,
    baseUrl: deriveCopilotApiBaseUrlFromToken(payload.token) ?? "https://api.individual.githubcopilot.com"
  };
}
function isProviderApiKeyConfigured(params) {
  if ((0, _modelAuthEnvZyutsTwR.t)(params.provider)?.apiKey) return true;
  const agentDir = params.agentDir?.trim();
  if (!agentDir) return false;
  return (0, _profileListDRiyVI2U.n)((0, _storeCSOk8Bno.n)(agentDir, { allowKeychainPrompt: false }), params.provider).length > 0;
}
function listUsableProviderAuthProfileIds(params) {
  try {
    const agentDir = params.agentDir?.trim() || (0, _agentPathsUmbOEWUL.t)();
    const store = (0, _storeCSOk8Bno.n)(agentDir, { allowKeychainPrompt: false });
    return {
      agentDir,
      profileIds: (0, _order7oO26mfB.n)({
        cfg: params.cfg,
        store,
        provider: params.provider
      })
    };
  } catch {
    return {
      agentDir: "",
      profileIds: []
    };
  }
}
function isProviderAuthProfileConfigured(params) {
  return listUsableProviderAuthProfileIds(params).profileIds.length > 0;
}
async function resolveProviderAuthProfileApiKey(params) {
  const { agentDir, profileIds } = listUsableProviderAuthProfileIds(params);
  if (!agentDir || profileIds.length === 0) return;
  const store = (0, _storeCSOk8Bno.n)(agentDir, { allowKeychainPrompt: false });
  for (const profileId of profileIds) {
    const resolved = await (0, _oauthDoxNzd.t)({
      cfg: params.cfg,
      store,
      agentDir,
      profileId
    });
    if (resolved?.apiKey) return resolved.apiKey;
  }
}
//#endregion /* v9-84a16427b1b17464 */
