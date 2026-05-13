"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = resolvePluginAutoEnableCandidateReason;exports.i = configMayNeedPluginAutoEnable;exports.n = materializePluginAutoEnableCandidates;exports.r = detectPluginAutoEnableCandidates;exports.t = applyPluginAutoEnable;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
var _prototypeKeysBWjW0VW = require("./prototype-keys-BWjW0VW8.js");
var _stringNormalizationC5SGsaST = require("./string-normalization-C5SGsaST.js");
var _pluginMetadataSnapshotMEvRUosy = require("./plugin-metadata-snapshot-mEvRUosy.js");
var _idsPHiL43bp = require("./ids-PHiL43bp.js");
var _providerIdDIRgKpoh = require("./provider-id-DIRgKpoh.js");
var _modelRefsDDcinLNL = require("./model-refs-DDcinLNL.js");
var _chatMetaDIlVJJ5G = require("./chat-meta-DIlVJJ5G.js");
require("./registry-By_qtZ6R.js");
var _providersChCs1dXB = require("./providers-ChCs1dXB.js");
var _configPresenceBfpVV4_C = require("./config-presence-BfpVV4_C.js");
var _setupRegistryDSA33nXk = require("./setup-registry-DSA33nXk.js");
var _channelConfiguredBL9ACPhy = require("./channel-configured-BL9ACPhy.js");
var _pluginsAllowlistDz3tOOW = require("./plugins-allowlist-Dz3tOOW8.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/config/plugin-auto-enable.prefer-over.ts
const ENV_CATALOG_PATHS = ["OPENCLAW_PLUGIN_CATALOG_PATHS", "OPENCLAW_MPM_CATALOG_PATHS"];
function splitEnvPaths(value) {
  const trimmed = (0, _stringCoerceBje8XVt.c)(value) ?? "";
  if (!trimmed) return [];
  return (0, _stringNormalizationC5SGsaST.s)(trimmed.split(/[;,]/g).flatMap((chunk) => chunk.split(_nodePath.default.delimiter)));
}
function resolveExternalCatalogPaths(env) {
  for (const key of ENV_CATALOG_PATHS) {
    const raw = (0, _stringCoerceBje8XVt.c)(env[key]);
    if (raw) return splitEnvPaths(raw);
  }
  const configDir = (0, _utilsD5swhEXt.d)(env);
  return [
  _nodePath.default.join(configDir, "mpm", "plugins.json"),
  _nodePath.default.join(configDir, "mpm", "catalog.json"),
  _nodePath.default.join(configDir, "plugins", "catalog.json")];

}
function parseExternalCatalogChannelEntries(raw) {
  const list = (() => {
    if (Array.isArray(raw)) return raw;
    if (!(0, _utilsD5swhEXt.c)(raw)) return [];
    const entries = raw.entries ?? raw.packages ?? raw.plugins;
    return Array.isArray(entries) ? entries : [];
  })();
  const channels = [];
  for (const entry of list) {
    if (!(0, _utilsD5swhEXt.c)(entry) || !(0, _utilsD5swhEXt.c)(entry.openclaw) || !(0, _utilsD5swhEXt.c)(entry.openclaw.channel)) continue;
    const channel = entry.openclaw.channel;
    const id = (0, _stringCoerceBje8XVt.c)(channel.id) ?? "";
    if (!id) continue;
    const preferOver = Array.isArray(channel.preferOver) ? channel.preferOver.filter((value) => typeof value === "string") : [];
    channels.push({
      id,
      preferOver
    });
  }
  return channels;
}
function resolveExternalCatalogPreferOver(channelId, env) {
  for (const rawPath of resolveExternalCatalogPaths(env)) {
    const resolved = (0, _utilsD5swhEXt.p)(rawPath, env);
    if (!_nodeFs.default.existsSync(resolved)) continue;
    try {
      const channel = parseExternalCatalogChannelEntries(JSON.parse(_nodeFs.default.readFileSync(resolved, "utf-8"))).find((entry) => entry.id === channelId);
      if (channel) return channel.preferOver;
    } catch {}
  }
  return [];
}
function resolveBuiltInChannelPreferOver(channelId) {
  const builtInChannelId = (0, _idsPHiL43bp.r)(channelId);
  if (!builtInChannelId) return [];
  return (0, _chatMetaDIlVJJ5G.t)(builtInChannelId)?.preferOver ?? [];
}
function resolvePreferredOverIds(candidate, env, registry) {
  const channelId = candidate.kind === "channel-configured" ? candidate.channelId : candidate.pluginId;
  const installedPlugin = registry.plugins.find((record) => record.id === candidate.pluginId);
  const manifestChannelPreferOver = installedPlugin?.channelConfigs?.[channelId]?.preferOver;
  if (manifestChannelPreferOver?.length) return [...manifestChannelPreferOver];
  const installedChannelMeta = installedPlugin?.channelCatalogMeta;
  if (installedChannelMeta?.preferOver?.length) return [...installedChannelMeta.preferOver];
  const builtInChannelPreferOver = resolveBuiltInChannelPreferOver(channelId);
  if (builtInChannelPreferOver.length) return [...builtInChannelPreferOver];
  return resolveExternalCatalogPreferOver(channelId, env);
}
function getPluginAutoEnableCandidateCacheKey(candidate) {
  return `${candidate.pluginId}:${candidate.kind === "channel-configured" ? candidate.channelId : candidate.pluginId}`;
}
function shouldSkipPreferredPluginAutoEnable(params) {
  const getPreferredOverIds = (candidate) => {
    const cacheKey = getPluginAutoEnableCandidateCacheKey(candidate);
    const cached = params.preferOverCache.get(cacheKey);
    if (cached) return cached;
    const resolved = resolvePreferredOverIds(candidate, params.env, params.registry);
    params.preferOverCache.set(cacheKey, resolved);
    return resolved;
  };
  for (const other of params.configured) {
    if (other.pluginId === params.entry.pluginId) continue;
    if (params.isPluginDenied(params.config, other.pluginId) || params.isPluginExplicitlyDisabled(params.config, other.pluginId)) continue;
    if (getPreferredOverIds(other).includes(params.entry.pluginId)) return true;
  }
  return false;
}
//#endregion
//#region src/config/plugin-auto-enable.shared.ts
const EMPTY_PLUGIN_MANIFEST_REGISTRY = {
  plugins: [],
  diagnostics: []
};
function resolveAutoEnableProviderPluginIds(registry) {
  const entries = /* @__PURE__ */new Map();
  for (const plugin of registry.plugins) for (const providerId of plugin.autoEnableWhenConfiguredProviders ?? []) if (!entries.has(providerId)) entries.set(providerId, plugin.id);
  return Object.fromEntries(entries);
}
function extractProviderFromModelRef(value) {
  const trimmed = value.trim();
  const slash = trimmed.indexOf("/");
  if (slash <= 0) return null;
  return (0, _providerIdDIRgKpoh.r)(trimmed.slice(0, slash));
}
function hasConfiguredEmbeddedHarnessRuntime(cfg, env) {
  return (0, _configPresenceBfpVV4_C.o)(cfg, env).length > 0;
}
function resolveAgentHarnessOwnerPluginIds(registry, runtime) {
  const normalizedRuntime = (0, _stringCoerceBje8XVt.s)(runtime);
  if (!normalizedRuntime) return [];
  return registry.plugins.filter((plugin) => [...(plugin.activation?.onAgentHarnesses ?? []), ...(plugin.cliBackends ?? [])].some((entry) => (0, _stringCoerceBje8XVt.s)(entry) === normalizedRuntime)).map((plugin) => plugin.id).toSorted((left, right) => left.localeCompare(right));
}
function isProviderConfigured(cfg, providerId) {
  const normalized = (0, _providerIdDIRgKpoh.r)(providerId);
  const profiles = cfg.auth?.profiles;
  if (profiles && typeof profiles === "object") for (const profile of Object.values(profiles)) {
    if (!(0, _utilsD5swhEXt.c)(profile)) continue;
    if ((0, _providerIdDIRgKpoh.r)(profile.provider ?? "") === normalized) return true;
  }
  const providerConfig = cfg.models?.providers;
  if (providerConfig && typeof providerConfig === "object") {
    for (const key of Object.keys(providerConfig)) if ((0, _providerIdDIRgKpoh.r)(key) === normalized) return true;
  }
  for (const { value: ref } of (0, _modelRefsDDcinLNL.n)(cfg, { includeChannelModelOverrides: false })) {
    const provider = extractProviderFromModelRef(ref);
    if (provider && provider === normalized) return true;
  }
  return false;
}
function hasPluginOwnedWebSearchConfig(cfg, pluginId) {
  const pluginConfig = cfg.plugins?.entries?.[pluginId]?.config;
  return (0, _utilsD5swhEXt.c)(pluginConfig) && (0, _utilsD5swhEXt.c)(pluginConfig.webSearch);
}
function hasPluginOwnedWebFetchConfig(cfg, pluginId) {
  const pluginConfig = cfg.plugins?.entries?.[pluginId]?.config;
  return (0, _utilsD5swhEXt.c)(pluginConfig) && (0, _utilsD5swhEXt.c)(pluginConfig.webFetch);
}
function resolvePluginOwnedToolConfigKeys(plugin) {
  if ((plugin.contracts?.tools?.length ?? 0) === 0) return [];
  const properties = (0, _utilsD5swhEXt.c)(plugin.configSchema) ? plugin.configSchema.properties : void 0;
  if (!(0, _utilsD5swhEXt.c)(properties)) return [];
  return Object.keys(properties).filter((key) => key !== "webSearch" && key !== "webFetch");
}
function hasPluginOwnedToolConfig(cfg, plugin) {
  const pluginConfig = cfg.plugins?.entries?.[plugin.id]?.config;
  if (!(0, _utilsD5swhEXt.c)(pluginConfig)) return false;
  return resolvePluginOwnedToolConfigKeys(plugin).some((key) => pluginConfig[key] !== void 0);
}
function resolveProviderPluginsWithOwnedWebSearch(registry) {
  return registry.plugins.filter((plugin) => (plugin.providers?.length ?? 0) > 0).filter((plugin) => (plugin.contracts?.webSearchProviders?.length ?? 0) > 0);
}
function resolveProviderPluginsWithOwnedWebFetch(registry) {
  return registry.plugins.filter((plugin) => (plugin.contracts?.webFetchProviders?.length ?? 0) > 0);
}
function resolvePluginsWithOwnedToolConfig(registry) {
  return registry.plugins.filter((plugin) => (plugin.contracts?.tools?.length ?? 0) > 0);
}
function resolvePluginIdForConfiguredWebFetchProvider(providerId, registry) {
  const normalizedProviderId = (0, _stringCoerceBje8XVt.s)(providerId);
  if (!normalizedProviderId) return;
  return registry.plugins.find((plugin) => plugin.origin === "bundled" && (plugin.contracts?.webFetchProviders ?? []).some((candidate) => (0, _stringCoerceBje8XVt.s)(candidate) === normalizedProviderId))?.id;
}
function resolvePluginIdForConfiguredWebSearchProvider(providerId, registry) {
  const normalizedProviderId = (0, _stringCoerceBje8XVt.s)(providerId);
  if (!normalizedProviderId) return;
  return registry.plugins.find((plugin) => (plugin.contracts?.webSearchProviders ?? []).some((candidate) => (0, _stringCoerceBje8XVt.s)(candidate) === normalizedProviderId))?.id;
}
function normalizeManifestChannelId(channelId) {
  return (0, _idsPHiL43bp.r)(channelId) ?? channelId;
}
function getManifestChannelPreferOver(plugin, channelId) {
  return plugin.channelConfigs?.[channelId]?.preferOver ?? [];
}
function collectPluginIdsForConfiguredChannel(channelId, registry) {
  const normalizedChannelId = normalizeManifestChannelId(channelId);
  const builtInId = (0, _idsPHiL43bp.r)(normalizedChannelId);
  const claims = [];
  for (const record of registry.plugins) if ((record.channels ?? []).some((id) => normalizeManifestChannelId(id) === normalizedChannelId)) claims.push({
    plugin: record,
    preferOver: getManifestChannelPreferOver(record, normalizedChannelId)
  });
  if (claims.length === 0) return builtInId ? [builtInId] : [];
  const claimIds = new Set(claims.map((claim) => claim.plugin.id));
  if (builtInId) claimIds.add(builtInId);
  const preferredIds = /* @__PURE__ */new Set();
  for (const claim of claims) for (const preferredOverId of claim.preferOver) if (claimIds.has(preferredOverId)) {
    preferredIds.add(claim.plugin.id);
    preferredIds.add(preferredOverId);
  }
  if (preferredIds.size > 0) return [...preferredIds].toSorted((left, right) => left.localeCompare(right));
  return [claims[0]?.plugin.id ?? builtInId ?? normalizedChannelId];
}
function collectConfiguredChannelIds(cfg, env) {
  return (0, _configPresenceBfpVV4_C.a)(cfg, env, { includePersistedAuthState: false }).map((signal) => (0, _idsPHiL43bp.r)(signal.channelId) ?? signal.channelId).filter((channelId) => (0, _channelConfiguredBL9ACPhy.t)(cfg, channelId, env));
}
function hasConfiguredWebSearchPluginEntry(cfg) {
  const entries = cfg.plugins?.entries;
  return !!entries && typeof entries === "object" && Object.values(entries).some((entry) => (0, _utilsD5swhEXt.c)(entry) && (0, _utilsD5swhEXt.c)(entry.config) && (0, _utilsD5swhEXt.c)(entry.config.webSearch));
}
function hasConfiguredWebSearchProviderSelection(cfg) {
  const provider = cfg.tools?.web?.search?.provider;
  return cfg.tools?.web?.search?.enabled !== false && typeof provider === "string" && !!provider.trim();
}
function hasConfiguredWebFetchPluginEntry(cfg) {
  const entries = cfg.plugins?.entries;
  return !!entries && typeof entries === "object" && Object.values(entries).some((entry) => (0, _utilsD5swhEXt.c)(entry) && (0, _utilsD5swhEXt.c)(entry.config) && (0, _utilsD5swhEXt.c)(entry.config.webFetch));
}
function hasConfiguredPluginConfigEntry(cfg) {
  const entries = cfg.plugins?.entries;
  return !!entries && typeof entries === "object" && Object.values(entries).some((entry) => (0, _utilsD5swhEXt.c)(entry) && (0, _utilsD5swhEXt.c)(entry.config));
}
function listContainsNormalized(value, expected) {
  return Array.isArray(value) && value.some((entry) => (0, _stringCoerceBje8XVt.s)(entry) === expected);
}
function toolPolicyReferencesBrowser(value) {
  return (0, _utilsD5swhEXt.c)(value) && (listContainsNormalized(value.allow, "browser") || listContainsNormalized(value.alsoAllow, "browser"));
}
function hasBrowserToolReference(cfg) {
  if (toolPolicyReferencesBrowser(cfg.tools)) return true;
  const agentList = cfg.agents?.list;
  return Array.isArray(agentList) ? agentList.some((entry) => (0, _utilsD5swhEXt.c)(entry) && toolPolicyReferencesBrowser(entry.tools)) : false;
}
function collectConfiguredPluginEntryIds(cfg) {
  const entries = cfg.plugins?.entries;
  if (!entries || typeof entries !== "object") return [];
  return Object.keys(entries).map((pluginId) => pluginId.trim()).filter((pluginId) => pluginId && !isPluginEntryExplicitlyDisabled(cfg, pluginId));
}
function hasOwnPluginEntry(cfg, pluginId) {
  const entries = cfg.plugins?.entries;
  return !!entries && typeof entries === "object" && Object.hasOwn(entries, pluginId);
}
function isPluginEntryExplicitlyDisabled(cfg, pluginId) {
  return cfg.plugins?.entries?.[pluginId]?.enabled === false;
}
function hasNonDisabledPluginEntry(cfg, pluginId) {
  if (!hasOwnPluginEntry(cfg, pluginId)) return false;
  return !isPluginEntryExplicitlyDisabled(cfg, pluginId);
}
function hasBrowserSetupAutoEnableRelevantConfig(cfg) {
  if (cfg.browser?.enabled === false || isPluginEntryExplicitlyDisabled(cfg, "browser")) return false;
  if ((0, _utilsD5swhEXt.c)(cfg.browser)) return true;
  if (hasNonDisabledPluginEntry(cfg, "browser")) return true;
  return hasBrowserToolReference(cfg);
}
function hasAcpxSetupAutoEnableRelevantConfig(cfg) {
  if (isPluginEntryExplicitlyDisabled(cfg, "acpx")) return false;
  if (!(0, _utilsD5swhEXt.c)(cfg.acp)) return false;
  const backend = (0, _stringCoerceBje8XVt.s)(cfg.acp.backend);
  return (cfg.acp.enabled === true || (0, _utilsD5swhEXt.c)(cfg.acp.dispatch) && cfg.acp.dispatch.enabled === true || backend === "acpx") && (!backend || backend === "acpx");
}
function hasXaiSetupAutoEnableRelevantConfig(cfg) {
  if (isPluginEntryExplicitlyDisabled(cfg, "xai")) return false;
  const pluginConfig = cfg.plugins?.entries?.xai?.config;
  return (0, _utilsD5swhEXt.c)(pluginConfig) && ((0, _utilsD5swhEXt.c)(pluginConfig.xSearch) || (0, _utilsD5swhEXt.c)(pluginConfig.codeExecution)) || (0, _utilsD5swhEXt.c)(cfg.tools?.web) && (0, _utilsD5swhEXt.c)(cfg.tools.web.x_search);
}
function resolveRelevantSetupAutoEnablePluginIds(cfg) {
  const pluginIds = new Set(collectConfiguredPluginEntryIds(cfg));
  if (hasBrowserSetupAutoEnableRelevantConfig(cfg)) pluginIds.add("browser");
  if (hasAcpxSetupAutoEnableRelevantConfig(cfg)) pluginIds.add("acpx");
  if (hasXaiSetupAutoEnableRelevantConfig(cfg)) pluginIds.add("xai");
  return [...pluginIds].toSorted((left, right) => left.localeCompare(right));
}
function hasSetupAutoEnableRelevantConfig(cfg) {
  return hasBrowserSetupAutoEnableRelevantConfig(cfg) || hasAcpxSetupAutoEnableRelevantConfig(cfg) || hasXaiSetupAutoEnableRelevantConfig(cfg) || hasConfiguredPluginConfigEntry(cfg);
}
function hasPluginEntries(cfg) {
  const entries = cfg.plugins?.entries;
  return !!entries && typeof entries === "object" && Object.keys(entries).length > 0;
}
function hasPluginAllowlistWithMaterialEntries(cfg) {
  if (!Array.isArray(cfg.plugins?.allow) || cfg.plugins.allow.length === 0 || !hasPluginEntries(cfg)) return false;
  const entries = cfg.plugins?.entries;
  if (!entries || typeof entries !== "object") return false;
  return Object.values(entries).some(hasMaterialPluginEntryConfig);
}
function hasConfiguredProviderModelOrHarness(cfg, env) {
  if (cfg.auth?.profiles && Object.keys(cfg.auth.profiles).length > 0) return true;
  if (cfg.models?.providers && Object.keys(cfg.models.providers).length > 0) return true;
  if ((0, _modelRefsDDcinLNL.n)(cfg, { includeChannelModelOverrides: false }).length > 0) return true;
  return hasConfiguredEmbeddedHarnessRuntime(cfg, env);
}
function arePluginsGloballyDisabled(cfg) {
  return cfg.plugins?.enabled === false;
}
function configMayNeedPluginManifestRegistry(cfg, env) {
  if (arePluginsGloballyDisabled(cfg)) return false;
  if (hasPluginAllowlistWithMaterialEntries(cfg)) return true;
  if (hasConfiguredPluginConfigEntry(cfg)) return true;
  if (hasConfiguredProviderModelOrHarness(cfg, env)) return true;
  if (hasConfiguredWebSearchProviderSelection(cfg)) return true;
  const configuredChannels = cfg.channels;
  if (!configuredChannels || typeof configuredChannels !== "object") return false;
  for (const key of Object.keys(configuredChannels)) {
    if (key === "defaults" || key === "modelByChannel") continue;
    return true;
  }
  return false;
}
function configMayNeedPluginAutoEnable(cfg, env) {
  if (arePluginsGloballyDisabled(cfg)) return false;
  if (hasPluginAllowlistWithMaterialEntries(cfg)) return true;
  if (hasConfiguredPluginConfigEntry(cfg)) return true;
  if ((0, _configPresenceBfpVV4_C.n)(cfg, env, { includePersistedAuthState: false })) return true;
  if (hasConfiguredProviderModelOrHarness(cfg, env)) return true;
  if (hasConfiguredWebSearchProviderSelection(cfg) || hasConfiguredWebSearchPluginEntry(cfg) || hasConfiguredWebFetchPluginEntry(cfg)) return true;
  if (!hasSetupAutoEnableRelevantConfig(cfg)) return false;
  return (0, _setupRegistryDSA33nXk.n)({
    config: cfg,
    env,
    pluginIds: resolveRelevantSetupAutoEnablePluginIds(cfg)
  }).length > 0;
}
function resolvePluginAutoEnableCandidateReason(candidate) {
  switch (candidate.kind) {
    case "channel-configured":return `${candidate.channelId} configured`;
    case "provider-auth-configured":return `${candidate.providerId} auth configured`;
    case "provider-model-configured":return `${candidate.modelRef} model configured`;
    case "agent-harness-runtime-configured":return `${candidate.runtime} agent runtime configured`;
    case "web-search-provider-selected":return `${candidate.providerId} web search provider selected`;
    case "web-fetch-provider-selected":return `${candidate.providerId} web fetch provider selected`;
    case "plugin-web-search-configured":return `${candidate.pluginId} web search configured`;
    case "plugin-web-fetch-configured":return `${candidate.pluginId} web fetch configured`;
    case "plugin-tool-configured":return `${candidate.pluginId} tool configured`;
    case "setup-auto-enable":return candidate.reason;
  }
  throw new Error("Unsupported plugin auto-enable candidate");
}
function resolveConfiguredPluginAutoEnableCandidates(params) {
  const changes = [];
  for (const channelId of collectConfiguredChannelIds(params.config, params.env)) for (const pluginId of collectPluginIdsForConfiguredChannel(channelId, params.registry)) changes.push({
    pluginId,
    kind: "channel-configured",
    channelId
  });
  for (const [providerId, pluginId] of Object.entries(resolveAutoEnableProviderPluginIds(params.registry))) if (isProviderConfigured(params.config, providerId)) changes.push({
    pluginId,
    kind: "provider-auth-configured",
    providerId
  });
  for (const { value: modelRef } of (0, _modelRefsDDcinLNL.n)(params.config, { includeChannelModelOverrides: false })) {
    const owningPluginIds = (0, _providersChCs1dXB.l)({
      model: modelRef,
      config: params.config,
      env: params.env,
      manifestRegistry: params.registry
    });
    if (owningPluginIds?.length === 1) changes.push({
      pluginId: owningPluginIds[0],
      kind: "provider-model-configured",
      modelRef
    });
  }
  for (const runtime of (0, _configPresenceBfpVV4_C.o)(params.config, params.env)) {
    const pluginIds = resolveAgentHarnessOwnerPluginIds(params.registry, runtime);
    for (const pluginId of pluginIds) changes.push({
      pluginId,
      kind: "agent-harness-runtime-configured",
      runtime
    });
  }
  const webSearchConfig = params.config.tools?.web?.search;
  const webSearchProvider = webSearchConfig?.enabled !== false && typeof webSearchConfig?.provider === "string" ? webSearchConfig.provider : void 0;
  const webSearchPluginId = resolvePluginIdForConfiguredWebSearchProvider(webSearchProvider, params.registry);
  if (webSearchPluginId) changes.push({
    pluginId: webSearchPluginId,
    kind: "web-search-provider-selected",
    providerId: (0, _stringCoerceBje8XVt.s)(webSearchProvider) ?? ""
  });
  const webFetchProvider = typeof params.config.tools?.web?.fetch?.provider === "string" ? params.config.tools.web.fetch.provider : void 0;
  const webFetchPluginId = resolvePluginIdForConfiguredWebFetchProvider(webFetchProvider, params.registry);
  if (webFetchPluginId) changes.push({
    pluginId: webFetchPluginId,
    kind: "web-fetch-provider-selected",
    providerId: (0, _stringCoerceBje8XVt.s)(webFetchProvider) ?? ""
  });
  for (const plugin of resolveProviderPluginsWithOwnedWebSearch(params.registry)) {
    const pluginId = plugin.id;
    if (hasPluginOwnedWebSearchConfig(params.config, pluginId)) changes.push({
      pluginId,
      kind: "plugin-web-search-configured"
    });
  }
  for (const plugin of resolvePluginsWithOwnedToolConfig(params.registry)) {
    const pluginId = plugin.id;
    if (hasPluginOwnedToolConfig(params.config, plugin)) changes.push({
      pluginId,
      kind: "plugin-tool-configured"
    });
  }
  for (const plugin of resolveProviderPluginsWithOwnedWebFetch(params.registry)) {
    const pluginId = plugin.id;
    if (hasPluginOwnedWebFetchConfig(params.config, pluginId)) changes.push({
      pluginId,
      kind: "plugin-web-fetch-configured"
    });
  }
  if (hasSetupAutoEnableRelevantConfig(params.config)) {
    const manifestMatchedPluginIds = new Set(changes.map((entry) => entry.pluginId));
    const setupPluginIds = resolveRelevantSetupAutoEnablePluginIds(params.config).filter((pluginId) => !manifestMatchedPluginIds.has(pluginId));
    for (const entry of (0, _setupRegistryDSA33nXk.n)({
      config: params.config,
      env: params.env,
      pluginIds: setupPluginIds
    })) changes.push({
      pluginId: entry.pluginId,
      kind: "setup-auto-enable",
      reason: entry.reason
    });
  }
  return changes;
}
function isPluginExplicitlyDisabled(cfg, pluginId) {
  const builtInChannelId = (0, _idsPHiL43bp.r)(pluginId);
  if (builtInChannelId) {
    const channelConfig = cfg.channels?.[builtInChannelId];
    if (channelConfig && typeof channelConfig === "object" && !Array.isArray(channelConfig) && channelConfig.enabled === false) return true;
  }
  return cfg.plugins?.entries?.[pluginId]?.enabled === false;
}
function isPluginDenied(cfg, pluginId) {
  const deny = cfg.plugins?.deny;
  return Array.isArray(deny) && deny.includes(pluginId);
}
function isPluginExplicitlySelected(cfg, pluginId) {
  const allow = cfg.plugins?.allow;
  if (Array.isArray(allow) && allow.includes(pluginId)) return true;
  return hasMaterialPluginEntryConfig(cfg.plugins?.entries?.[pluginId]);
}
function disableImplicitPreferredOverPlugin(params) {
  if (isPluginExplicitlySelected(params.originalConfig, params.pluginId)) return params.config;
  if (!(0, _idsPHiL43bp.r)(params.pluginId) && !isKnownPluginId(params.pluginId, params.manifestRegistry)) return params.config;
  const existingEntry = params.config.plugins?.entries?.[params.pluginId];
  return {
    ...params.config,
    plugins: {
      ...params.config.plugins,
      entries: {
        ...params.config.plugins?.entries,
        [params.pluginId]: {
          ...(existingEntry && typeof existingEntry === "object" ? existingEntry : {}),
          enabled: false
        }
      }
    }
  };
}
function isBuiltInChannelAlreadyEnabled(cfg, channelId) {
  const channelConfig = cfg.channels?.[channelId];
  return !!channelConfig && typeof channelConfig === "object" && !Array.isArray(channelConfig) && channelConfig.enabled === true;
}
function resolveAutoEnableChannelId(params) {
  const builtInChannelId = (0, _idsPHiL43bp.r)(params.entry.pluginId);
  if (builtInChannelId) return builtInChannelId;
  if (params.entry.kind !== "channel-configured") return null;
  const plugin = params.manifestRegistry.plugins.find((record) => record.id === params.entry.pluginId);
  if (plugin?.origin !== "bundled") return null;
  const channelId = normalizeManifestChannelId(params.entry.channelId);
  return (plugin.channels ?? []).some((id) => normalizeManifestChannelId(id) === channelId) ? channelId : null;
}
function registerPluginEntry(cfg, entry, manifestRegistry) {
  const builtInChannelId = resolveAutoEnableChannelId({
    entry,
    manifestRegistry
  });
  if (builtInChannelId) {
    const existing = cfg.channels?.[builtInChannelId];
    const existingRecord = existing && typeof existing === "object" && !Array.isArray(existing) ? existing : {};
    return {
      ...cfg,
      channels: {
        ...cfg.channels,
        [builtInChannelId]: {
          ...existingRecord,
          enabled: true
        }
      }
    };
  }
  return {
    ...cfg,
    plugins: {
      ...cfg.plugins,
      entries: {
        ...cfg.plugins?.entries,
        [entry.pluginId]: {
          ...cfg.plugins?.entries?.[entry.pluginId],
          enabled: true
        }
      }
    }
  };
}
function hasMaterialPluginEntryConfig(entry) {
  if (!(0, _utilsD5swhEXt.c)(entry)) return false;
  return entry.enabled === true || (0, _utilsD5swhEXt.c)(entry.config) || (0, _utilsD5swhEXt.c)(entry.hooks) || (0, _utilsD5swhEXt.c)(entry.subagent) || entry.apiKey !== void 0 || entry.env !== void 0;
}
function isKnownPluginId(pluginId, manifestRegistry) {
  if ((0, _idsPHiL43bp.r)(pluginId)) return true;
  return manifestRegistry.plugins.some((plugin) => plugin.id === pluginId);
}
function materializeConfiguredPluginEntryAllowlist(params) {
  let next = params.config;
  const allow = next.plugins?.allow;
  const entries = next.plugins?.entries;
  if (!Array.isArray(allow) || allow.length === 0 || !entries || typeof entries !== "object") return next;
  for (const pluginId of Object.keys(entries).toSorted((left, right) => left.localeCompare(right))) {
    const entry = entries[pluginId];
    if (!hasMaterialPluginEntryConfig(entry) || isPluginDenied(next, pluginId) || isPluginExplicitlyDisabled(next, pluginId) || allow.includes(pluginId) || !isKnownPluginId(pluginId, params.manifestRegistry)) continue;
    next = (0, _pluginsAllowlistDz3tOOW.t)(next, pluginId);
    params.changes.push(`${pluginId} plugin config present, added to plugin allowlist.`);
  }
  return next;
}
function resolveChannelAutoEnableDisplayLabel(entry, manifestRegistry) {
  const builtInChannelId = (0, _idsPHiL43bp.r)(entry.channelId);
  const plugin = manifestRegistry.plugins.find((record) => record.id === entry.pluginId);
  return (builtInChannelId ? (0, _chatMetaDIlVJJ5G.t)(builtInChannelId)?.label : void 0) ?? plugin?.channelConfigs?.[entry.channelId]?.label ?? plugin?.channelCatalogMeta?.label;
}
function formatAutoEnableChange(entry, manifestRegistry) {
  if (entry.kind === "channel-configured") {
    const label = resolveChannelAutoEnableDisplayLabel(entry, manifestRegistry);
    if (label) return `${label} configured, enabled automatically.`;
  }
  return `${resolvePluginAutoEnableCandidateReason(entry).trim()}, enabled automatically.`;
}
function resolvePluginAutoEnableManifestRegistry(params) {
  return params.manifestRegistry ?? (configMayNeedPluginManifestRegistry(params.config, params.env) ? (0, _pluginMetadataSnapshotMEvRUosy.r)({
    config: params.config,
    env: params.env
  }).manifestRegistry : EMPTY_PLUGIN_MANIFEST_REGISTRY);
}
function materializePluginAutoEnableCandidatesInternal(params) {
  let next = params.config ?? {};
  const changes = [];
  const autoEnabledReasons = /* @__PURE__ */new Map();
  if (next.plugins?.enabled === false) return {
    config: next,
    changes,
    autoEnabledReasons: {}
  };
  const preferOverCache = /* @__PURE__ */new Map();
  for (const entry of params.candidates) {
    const builtInChannelId = resolveAutoEnableChannelId({
      entry,
      manifestRegistry: params.manifestRegistry
    });
    if (isPluginDenied(next, entry.pluginId) || isPluginExplicitlyDisabled(next, entry.pluginId)) continue;
    if (shouldSkipPreferredPluginAutoEnable({
      config: next,
      entry,
      configured: params.candidates,
      env: params.env,
      registry: params.manifestRegistry,
      isPluginDenied,
      isPluginExplicitlyDisabled,
      preferOverCache
    })) {
      next = disableImplicitPreferredOverPlugin({
        config: next,
        originalConfig: params.config ?? {},
        pluginId: entry.pluginId,
        manifestRegistry: params.manifestRegistry
      });
      continue;
    }
    const allow = next.plugins?.allow;
    const allowMissing = Array.isArray(allow) && !allow.includes(entry.pluginId);
    if ((builtInChannelId != null ? isBuiltInChannelAlreadyEnabled(next, builtInChannelId) : next.plugins?.entries?.[entry.pluginId]?.enabled === true) && !allowMissing) continue;
    next = registerPluginEntry(next, entry, params.manifestRegistry);
    next = (0, _pluginsAllowlistDz3tOOW.t)(next, entry.pluginId);
    const reason = resolvePluginAutoEnableCandidateReason(entry);
    autoEnabledReasons.set(entry.pluginId, [...(autoEnabledReasons.get(entry.pluginId) ?? []), reason]);
    changes.push(formatAutoEnableChange(entry, params.manifestRegistry));
  }
  next = materializeConfiguredPluginEntryAllowlist({
    config: next,
    changes,
    manifestRegistry: params.manifestRegistry
  });
  const autoEnabledReasonRecord = Object.create(null);
  for (const [pluginId, reasons] of autoEnabledReasons) if (!(0, _prototypeKeysBWjW0VW.t)(pluginId)) autoEnabledReasonRecord[pluginId] = [...reasons];
  return {
    config: next,
    changes,
    autoEnabledReasons: autoEnabledReasonRecord
  };
}
//#endregion
//#region src/config/plugin-auto-enable.detect.ts
function detectPluginAutoEnableCandidates(params) {
  const env = params.env ?? process.env;
  const config = params.config ?? {};
  if (!configMayNeedPluginAutoEnable(config, env)) return [];
  return resolveConfiguredPluginAutoEnableCandidates({
    config,
    env,
    registry: resolvePluginAutoEnableManifestRegistry({
      config,
      env,
      manifestRegistry: params.manifestRegistry
    })
  });
}
//#endregion
//#region src/config/plugin-auto-enable.apply.ts
function materializePluginAutoEnableCandidates(params) {
  const env = params.env ?? process.env;
  const config = params.config ?? {};
  const manifestRegistry = resolvePluginAutoEnableManifestRegistry({
    config,
    env,
    manifestRegistry: params.manifestRegistry
  });
  return materializePluginAutoEnableCandidatesInternal({
    config,
    candidates: params.candidates,
    env,
    manifestRegistry
  });
}
function applyPluginAutoEnable(params) {
  const candidates = detectPluginAutoEnableCandidates(params);
  return materializePluginAutoEnableCandidates({
    config: params.config,
    candidates,
    env: params.env,
    manifestRegistry: params.manifestRegistry
  });
}
//#endregion /* v9-4091aedbe2d98c45 */
