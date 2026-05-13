"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = resolvePluginDiscoveryProvidersRuntime;var _pluginModuleLoaderCacheB600Kx = require("./plugin-module-loader-cache-B60-0Kx3.js");
var _manifestContractEligibilityBuQOyv = require("./manifest-contract-eligibility-BuQOyv7-.js");
var _providersChCs1dXB = require("./providers-ChCs1dXB.js");
var _pluginLoadProfileCX9TjsiD = require("./plugin-load-profile-CX9TjsiD.js");
var _providersRuntimeHbUzyUP = require("./providers.runtime-hb-uzyUP.js");
//#region src/plugins/source-loader.ts
function createPluginSourceLoader() {
  const loaders = (0, _pluginModuleLoaderCacheB600Kx.t)();
  return (modulePath) => {
    const sourceLoader = (0, _pluginModuleLoaderCacheB600Kx.r)({
      cache: loaders,
      modulePath,
      importerUrl: "file:///opt/homebrew/lib/node_modules/openclaw/dist/provider-discovery.runtime-_FlNT3d8.js",
      loaderFilename: "file:///opt/homebrew/lib/node_modules/openclaw/dist/provider-discovery.runtime-_FlNT3d8.js"
    });
    return (0, _pluginLoadProfileCX9TjsiD.i)({
      pluginId: "(direct)",
      source: modulePath
    }, "source-loader", () => sourceLoader(modulePath));
  };
}
//#endregion
//#region src/plugins/provider-discovery.runtime.ts
function normalizeDiscoveryModule(value) {
  const resolved = value && typeof value === "object" && "default" in value && value.default !== void 0 ? value.default : value;
  if (Array.isArray(resolved)) return resolved;
  if (resolved && typeof resolved === "object" && "id" in resolved) return [resolved];
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const record = value;
    if (Array.isArray(record.providers)) return record.providers;
    if (record.provider) return [record.provider];
  }
  return [];
}
function hasLiveProviderDiscoveryHook(provider) {
  return typeof provider.catalog?.run === "function" || typeof provider.discovery?.run === "function";
}
function hasProviderAuthEnvCredential(plugin, env) {
  return Object.values(plugin.providerAuthEnvVars ?? {}).some((envVars) => envVars.some((name) => {
    const value = env[name]?.trim();
    return value !== void 0 && value !== "";
  }));
}
function dedupeSorted(values) {
  return [...new Set(values)].toSorted((left, right) => left.localeCompare(right));
}
function resolveProviderDiscoveryEntryPlugins(params) {
  const metadataSnapshot = params.pluginMetadataSnapshot ?? (0, _manifestContractEligibilityBuQOyv.s)({
    config: params.config ?? {},
    env: params.env ?? process.env,
    ...(params.workspaceDir ? { workspaceDir: params.workspaceDir } : {})
  });
  const registry = metadataSnapshot.index;
  const manifestRegistry = metadataSnapshot.manifestRegistry;
  const pluginIds = (0, _providersChCs1dXB.a)({
    ...params,
    registry,
    manifestRegistry
  });
  const pluginIdSet = new Set(pluginIds);
  const pluginRecords = manifestRegistry.plugins.filter((plugin) => pluginIdSet.has(plugin.id));
  const entryRecords = pluginRecords.filter((plugin) => plugin.providerDiscoverySource);
  const entryPluginIds = new Set(entryRecords.map((plugin) => plugin.id));
  if (entryRecords.length === 0) return {
    providers: [],
    complete: false,
    pluginRecords,
    entryPluginIds
  };
  const complete = entryRecords.length === pluginIdSet.size;
  if (params.requireCompleteDiscoveryEntryCoverage && !complete) return {
    providers: [],
    complete: false,
    pluginRecords,
    entryPluginIds
  };
  const loadSource = createPluginSourceLoader();
  const providers = [];
  for (const manifest of entryRecords) try {
    const moduleExport = loadSource(manifest.providerDiscoverySource);
    providers.push(...normalizeDiscoveryModule(moduleExport).map((provider) => Object.assign({}, provider, { pluginId: manifest.id })));
  } catch {
    return {
      providers: [],
      complete: false,
      pluginRecords,
      entryPluginIds
    };
  }
  return {
    providers,
    complete,
    pluginRecords,
    entryPluginIds
  };
}
function resolveSelectiveFullPluginIds(params) {
  const staticOnlyEntryPluginIds = params.entryProviders.filter((provider) => !hasLiveProviderDiscoveryHook(provider)).map((provider) => provider.pluginId).filter((pluginId) => typeof pluginId === "string" && pluginId !== "");
  const missingEntryCredentialPluginIds = params.entryResult.pluginRecords.filter((plugin) => !params.entryResult.entryPluginIds.has(plugin.id)).filter((plugin) => hasProviderAuthEnvCredential(plugin, params.env)).map((plugin) => plugin.id);
  return dedupeSorted([...staticOnlyEntryPluginIds, ...missingEntryCredentialPluginIds]);
}
function resolvePluginDiscoveryProvidersRuntime(params) {
  const env = params.env ?? process.env;
  const entryResult = resolveProviderDiscoveryEntryPlugins({
    ...params,
    env
  });
  if (params.discoveryEntriesOnly === true) return entryResult.providers;
  const liveEntryProviders = entryResult.providers.filter(hasLiveProviderDiscoveryHook);
  if (entryResult.complete && liveEntryProviders.length === entryResult.providers.length) return liveEntryProviders;
  if (params.onlyPluginIds === void 0 && entryResult.providers.length > 0) {
    const fullPluginIds = resolveSelectiveFullPluginIds({
      entryResult,
      entryProviders: entryResult.providers,
      env
    });
    const fullProviders = fullPluginIds.length > 0 ? (0, _providersRuntimeHbUzyUP.n)({
      ...params,
      env,
      onlyPluginIds: fullPluginIds,
      bundledProviderAllowlistCompat: true
    }) : [];
    return [...liveEntryProviders, ...fullProviders];
  }
  return (0, _providersRuntimeHbUzyUP.n)({
    ...params,
    env,
    bundledProviderAllowlistCompat: true
  });
}
//#endregion /* v9-ef56592d00d370f9 */
