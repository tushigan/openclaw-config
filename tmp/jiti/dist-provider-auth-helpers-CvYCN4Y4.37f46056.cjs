"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = writeOAuthCredentials;exports.n = buildApiKeyCredential;exports.r = upsertApiKeyProfile;exports.t = applyAuthProfileConfig;var _pathsC1_Y0cDn = require("./paths-C1_Y0cDn.js");
var _typesSecretsCL51SR4g = require("./types.secrets-CL51SR4g.js");
var _providerAuthAliasesChhMyI_u = require("./provider-auth-aliases-ChhMyI_u.js");
var _providerEnvVarsPk6C_sd = require("./provider-env-vars-pk6C_sd4.js");
var _agentPathsUmbOEWUL = require("./agent-paths-umbOEWUL.js");
var _normalizeSecretInputG30DI_5w = require("./normalize-secret-input-G30DI_5w.js");
var _identityCMUYJwmU = require("./identity-CMUYJwmU.js");
var _profilesCjRHFJUw = require("./profiles-CjRHFJUw.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/plugins/provider-auth-helpers.ts
const ENV_REF_PATTERN = /^\$\{([A-Z][A-Z0-9_]*)\}$/;
const resolveAuthAgentDir = (agentDir) => agentDir ?? (0, _agentPathsUmbOEWUL.t)();
function buildEnvSecretRef(id) {
  return {
    source: "env",
    provider: _typesSecretsCL51SR4g.t,
    id
  };
}
function parseEnvSecretRef(value) {
  const match = ENV_REF_PATTERN.exec(value);
  if (!match) return null;
  return buildEnvSecretRef(match[1]);
}
function resolveProviderDefaultEnvSecretRef(provider, config) {
  const envVar = (0, _providerEnvVarsPk6C_sd.t)(provider, {
    ...(config ? { config } : {}),
    includeUntrustedWorkspacePlugins: false
  })?.find((candidate) => candidate.trim().length > 0);
  if (!envVar) throw new Error(`Provider "${provider}" does not have a default env var mapping for secret-input-mode=ref.`);
  return buildEnvSecretRef(envVar);
}
function resolveApiKeySecretInput(provider, input, options) {
  if (options?.secretInputMode === "plaintext") return (0, _normalizeSecretInputG30DI_5w.n)(input);
  const coercedRef = (0, _typesSecretsCL51SR4g.o)(input);
  if (coercedRef) return coercedRef;
  const normalized = (0, _normalizeSecretInputG30DI_5w.n)(input);
  const inlineEnvRef = parseEnvSecretRef(normalized);
  if (inlineEnvRef) return inlineEnvRef;
  if (options?.secretInputMode === "ref") return resolveProviderDefaultEnvSecretRef(provider, options.config);
  return normalized;
}
function buildApiKeyCredential(provider, input, metadata, options) {
  const secretInput = resolveApiKeySecretInput(provider, input, options);
  if (typeof secretInput === "string") return {
    type: "api_key",
    provider,
    key: secretInput,
    ...(metadata ? { metadata } : {})
  };
  return {
    type: "api_key",
    provider,
    keyRef: secretInput,
    ...(metadata ? { metadata } : {})
  };
}
function upsertApiKeyProfile(params) {
  const profileId = params.profileId ?? (0, _identityCMUYJwmU.t)({ providerId: params.provider });
  (0, _profilesCjRHFJUw.a)({
    profileId,
    credential: buildApiKeyCredential(params.provider, params.input, params.metadata, params.options),
    agentDir: resolveAuthAgentDir(params.agentDir)
  });
  return profileId;
}
function applyAuthProfileConfig(cfg, params) {
  const normalizedProvider = (0, _providerAuthAliasesChhMyI_u.r)(params.provider, { config: cfg });
  const profiles = {
    ...cfg.auth?.profiles,
    [params.profileId]: {
      provider: params.provider,
      mode: params.mode,
      ...(params.email ? { email: params.email } : {}),
      ...(params.displayName ? { displayName: params.displayName } : {})
    }
  };
  const configuredProviderProfiles = Object.entries(cfg.auth?.profiles ?? {}).filter(([, profile]) => (0, _providerAuthAliasesChhMyI_u.r)(profile.provider, { config: cfg }) === normalizedProvider).map(([profileId, profile]) => ({
    profileId,
    mode: profile.mode
  }));
  const matchingProviderOrderEntries = Object.entries(cfg.auth?.order ?? {}).filter(([providerId]) => (0, _providerAuthAliasesChhMyI_u.r)(providerId, { config: cfg }) === normalizedProvider);
  const existingProviderOrder = matchingProviderOrderEntries.length > 0 ? [...new Set(matchingProviderOrderEntries.flatMap(([, order]) => order))] : void 0;
  const preferProfileFirst = params.preferProfileFirst ?? true;
  const reorderedProviderOrder = existingProviderOrder && preferProfileFirst ? [params.profileId, ...existingProviderOrder.filter((profileId) => profileId !== params.profileId)] : existingProviderOrder;
  const hasMixedConfiguredModes = configuredProviderProfiles.some(({ profileId, mode }) => profileId !== params.profileId && mode !== params.mode);
  const derivedProviderOrder = existingProviderOrder === void 0 && preferProfileFirst && hasMixedConfiguredModes ? [params.profileId, ...configuredProviderProfiles.map(({ profileId }) => profileId).filter((profileId) => profileId !== params.profileId)] : void 0;
  const baseOrder = matchingProviderOrderEntries.length > 0 ? Object.fromEntries(Object.entries(cfg.auth?.order ?? {}).filter(([providerId]) => (0, _providerAuthAliasesChhMyI_u.r)(providerId, { config: cfg }) !== normalizedProvider)) : cfg.auth?.order;
  const order = existingProviderOrder !== void 0 ? {
    ...baseOrder,
    [normalizedProvider]: reorderedProviderOrder?.includes(params.profileId) ? reorderedProviderOrder : [...(reorderedProviderOrder ?? []), params.profileId]
  } : derivedProviderOrder ? {
    ...baseOrder,
    [normalizedProvider]: derivedProviderOrder
  } : baseOrder;
  return {
    ...cfg,
    auth: {
      ...cfg.auth,
      profiles,
      ...(order ? { order } : {})
    }
  };
}
/** Resolve real path, returning null if the target doesn't exist. */
function safeRealpathSync(dir) {
  try {
    return _nodeFs.default.realpathSync(_nodePath.default.resolve(dir));
  } catch {
    return null;
  }
}
function resolveSiblingAgentDirs(primaryAgentDir) {
  const normalized = _nodePath.default.resolve(primaryAgentDir);
  const parentOfAgent = _nodePath.default.dirname(normalized);
  const candidateAgentsRoot = _nodePath.default.dirname(parentOfAgent);
  const agentsRoot = _nodePath.default.basename(normalized) === "agent" && _nodePath.default.basename(candidateAgentsRoot) === "agents" ? candidateAgentsRoot : _nodePath.default.join((0, _pathsC1_Y0cDn.v)(), "agents");
  const discovered = (() => {
    try {
      return _nodeFs.default.readdirSync(agentsRoot, { withFileTypes: true });
    } catch {
      return [];
    }
  })().filter((entry) => entry.isDirectory() || entry.isSymbolicLink()).map((entry) => _nodePath.default.join(agentsRoot, entry.name, "agent"));
  const seen = /* @__PURE__ */new Set();
  const result = [];
  for (const dir of [normalized, ...discovered]) {
    const real = safeRealpathSync(dir);
    if (real && !seen.has(real)) {
      seen.add(real);
      result.push(real);
    }
  }
  return result;
}
async function writeOAuthCredentials(provider, creds, agentDir, options) {
  const email = typeof creds.email === "string" && creds.email.trim() ? creds.email.trim() : "default";
  const profileId = (0, _identityCMUYJwmU.t)({
    providerId: provider,
    profileName: options?.profileName ?? email
  });
  const resolvedAgentDir = _nodePath.default.resolve(resolveAuthAgentDir(agentDir));
  const targetAgentDirs = options?.syncSiblingAgents ? resolveSiblingAgentDirs(resolvedAgentDir) : [resolvedAgentDir];
  const credential = {
    type: "oauth",
    provider,
    ...creds,
    ...(options?.displayName ? { displayName: options.displayName } : {})
  };
  (0, _profilesCjRHFJUw.a)({
    profileId,
    credential,
    agentDir: resolvedAgentDir
  });
  if (options?.syncSiblingAgents) {
    const primaryReal = safeRealpathSync(resolvedAgentDir);
    for (const targetAgentDir of targetAgentDirs) {
      const targetReal = safeRealpathSync(targetAgentDir);
      if (targetReal && primaryReal && targetReal === primaryReal) continue;
      try {
        (0, _profilesCjRHFJUw.a)({
          profileId,
          credential,
          agentDir: targetAgentDir
        });
      } catch {}
    }
  }
  return profileId;
}
//#endregion /* v9-e4559ef3d43578dc */
