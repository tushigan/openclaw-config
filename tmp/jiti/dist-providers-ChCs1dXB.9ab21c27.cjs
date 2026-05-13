"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = resolveDiscoveredProviderPluginIds;exports.c = resolveExternalAuthProfileProviderPluginIds;exports.d = resolveOwningPluginIdsForProvider;exports.f = withBundledProviderVitestCompat;exports.i = resolveDiscoverableProviderOwnerPluginIds;exports.l = resolveOwningPluginIdsForModelRef;exports.n = resolveBundledProviderCompatPluginIds;exports.o = resolveEnabledProviderPluginIds;exports.r = resolveCatalogHookProviderPluginIds;exports.s = resolveExternalAuthProfileCompatFallbackPluginIds;exports.t = resolveActivatableProviderOwnerPluginIds;exports.u = resolveOwningPluginIdsForModelRefs;var _installedPluginIndexStoreDH9sPamj = require("./installed-plugin-index-store-DH9sPamj.js");
var _configStateWKtsQXM = require("./config-state-wKtsQXM5.js");
var _manifestRegistryInstalled5Jxol4QJ = require("./manifest-registry-installed-5Jxol4QJ.js");
var _pluginRegistryCutMFnk = require("./plugin-registry-Cut-MFnk.js");
var _providerIdDIRgKpoh = require("./provider-id-DIRgKpoh.js");
var _bundledCompatBCabKG5D = require("./bundled-compat-BCabKG5D.js");
var _modelRefProfileCtGPNXes = require("./model-ref-profile-CtGPNXes.js");
var _bundledDEq7iy1i = require("./bundled-DEq7iy1i.js");
var _packageStateProbesAnoN2cCB = require("./package-state-probes-AnoN2cCB.js");
//#region src/plugins/providers.ts
function loadProviderRegistrySnapshot(params) {
  if (params.registry) return params.registry;
  return (0, _pluginRegistryCutMFnk.p)({
    config: params.config,
    workspaceDir: params.workspaceDir,
    env: params.env
  });
}
function loadScopedProviderRegistry(params) {
  return {
    registry: loadProviderRegistrySnapshot(params),
    onlyPluginIdSet: (0, _packageStateProbesAnoN2cCB.r)(params.onlyPluginIds)
  };
}
function listRegistryPluginIds(registry, predicate) {
  return registry.plugins.filter(predicate).map((plugin) => plugin.pluginId).toSorted((left, right) => left.localeCompare(right));
}
function resolveProviderSurfacePluginIdSet(params) {
  return new Set(resolveManifestRegistry({
    ...params,
    includeDisabled: true
  }).plugins.flatMap((plugin) => plugin.providers.length > 0 ? [plugin.id] : []));
}
function resolveProviderOwnerPluginIds(params) {
  if (params.pluginIds.length === 0) return [];
  const pluginIdSet = new Set(params.pluginIds);
  const registry = loadProviderRegistrySnapshot(params);
  const normalizedConfig = (0, _pluginRegistryCutMFnk.r)(params.config?.plugins, registry);
  return listRegistryPluginIds(registry, (plugin) => pluginIdSet.has(plugin.pluginId) && params.isEligible(plugin, normalizedConfig));
}
function resolveEffectiveRegistryPluginActivation(params) {
  return (0, _configStateWKtsQXM.l)({
    id: params.plugin.pluginId,
    origin: params.plugin.origin,
    config: params.normalizedConfig,
    rootConfig: params.rootConfig,
    enabledByDefault: (0, _installedPluginIndexStoreDH9sPamj.g)(params.plugin)
  });
}
function toManifestOwnerRecord(plugin) {
  return {
    id: plugin.pluginId,
    origin: plugin.origin,
    enabledByDefault: (0, _installedPluginIndexStoreDH9sPamj.g)(plugin)
  };
}
function withBundledProviderVitestCompat(params) {
  return (0, _bundledCompatBCabKG5D.r)(params);
}
function resolveBundledProviderCompatPluginIds(params) {
  if (params.manifestRegistry) {
    const onlyPluginIdSet = (0, _packageStateProbesAnoN2cCB.r)(params.onlyPluginIds);
    return params.manifestRegistry.plugins.filter((plugin) => plugin.origin === "bundled" && plugin.providers.length > 0 && (!onlyPluginIdSet || onlyPluginIdSet.has(plugin.id))).map((plugin) => plugin.id).toSorted((left, right) => left.localeCompare(right));
  }
  const { registry, onlyPluginIdSet } = loadScopedProviderRegistry(params);
  const providerSurfacePluginIds = resolveProviderSurfacePluginIdSet({
    ...params,
    registry
  });
  return listRegistryPluginIds(registry, (plugin) => plugin.origin === "bundled" && providerSurfacePluginIds.has(plugin.pluginId) && (!onlyPluginIdSet || onlyPluginIdSet.has(plugin.pluginId)));
}
function resolveEnabledProviderPluginIds(params) {
  const { registry, onlyPluginIdSet } = loadScopedProviderRegistry(params);
  const providerSurfacePluginIds = resolveProviderSurfacePluginIdSet({
    ...params,
    registry
  });
  const normalizedConfig = (0, _pluginRegistryCutMFnk.r)(params.config?.plugins, registry);
  return listRegistryPluginIds(registry, (plugin) => providerSurfacePluginIds.has(plugin.pluginId) && (!onlyPluginIdSet || onlyPluginIdSet.has(plugin.pluginId)) && resolveEffectiveRegistryPluginActivation({
    plugin,
    normalizedConfig,
    rootConfig: params.config
  }).activated);
}
function resolveExternalAuthProfileProviderPluginIds(params) {
  return resolveRegistryManifestContractPluginIds({
    ...params,
    contract: "externalAuthProviders"
  });
}
function resolveRegistryManifestContractPluginIds(params) {
  const { registry, onlyPluginIdSet } = loadScopedProviderRegistry(params);
  return resolveManifestRegistry({
    ...params,
    registry,
    includeDisabled: true
  }).plugins.filter((plugin) => {
    if (params.origin && plugin.origin !== params.origin) return false;
    if (onlyPluginIdSet && !onlyPluginIdSet.has(plugin.id)) return false;
    return (plugin.contracts?.[params.contract] ?? []).length > 0;
  }).map((plugin) => plugin.id).toSorted((left, right) => left.localeCompare(right));
}
function resolveExternalAuthProfileCompatFallbackPluginIds(params) {
  const declaredPluginIds = params.declaredPluginIds ?? new Set(resolveExternalAuthProfileProviderPluginIds(params));
  const registry = loadProviderRegistrySnapshot(params);
  const providerSurfacePluginIds = resolveProviderSurfacePluginIdSet({
    ...params,
    registry
  });
  const normalizedConfig = (0, _pluginRegistryCutMFnk.r)(params.config?.plugins, registry);
  return listRegistryPluginIds(registry, (plugin) => plugin.origin !== "bundled" && providerSurfacePluginIds.has(plugin.pluginId) && !declaredPluginIds.has(plugin.pluginId) && isProviderPluginEligibleForRuntimeOwnerActivation({
    plugin,
    normalizedConfig,
    rootConfig: params.config
  }));
}
function resolveDiscoveredProviderPluginIds(params) {
  const { registry, onlyPluginIdSet } = loadScopedProviderRegistry(params);
  const providerSurfacePluginIds = resolveProviderSurfacePluginIdSet({
    ...params,
    registry
  });
  const shouldFilterUntrustedWorkspacePlugins = params.includeUntrustedWorkspacePlugins === false;
  const shouldFilterBundledByAllowlist = params.config?.plugins?.bundledDiscovery !== "compat";
  const normalizedConfig = (0, _pluginRegistryCutMFnk.r)(params.config?.plugins, registry);
  return listRegistryPluginIds(registry, (plugin) => {
    if (!(providerSurfacePluginIds.has(plugin.pluginId) && (!onlyPluginIdSet || onlyPluginIdSet.has(plugin.pluginId)))) return false;
    return isProviderPluginEligibleForSetupDiscovery({
      plugin,
      shouldFilterUntrustedWorkspacePlugins,
      shouldFilterBundledByAllowlist,
      normalizedConfig,
      rootConfig: params.config
    });
  });
}
function isProviderPluginEligibleForSetupDiscovery(params) {
  if (params.plugin.origin === "workspace") {
    if (!params.shouldFilterUntrustedWorkspacePlugins) return true;
  } else if (!params.shouldFilterBundledByAllowlist) return true;
  if (!(0, _bundledDEq7iy1i.b)({
    plugin: toManifestOwnerRecord(params.plugin),
    normalizedConfig: params.normalizedConfig
  })) return false;
  if (params.plugin.origin === "bundled") return true;
  return (0, _bundledDEq7iy1i.v)({
    plugin: toManifestOwnerRecord(params.plugin),
    normalizedConfig: params.normalizedConfig,
    rootConfig: params.rootConfig
  });
}
function resolveDiscoverableProviderOwnerPluginIds(params) {
  const shouldFilterUntrustedWorkspacePlugins = params.includeUntrustedWorkspacePlugins === false;
  const shouldFilterBundledByAllowlist = params.config?.plugins?.bundledDiscovery !== "compat";
  return resolveProviderOwnerPluginIds({
    ...params,
    isEligible: (plugin, normalizedConfig) => isProviderPluginEligibleForSetupDiscovery({
      plugin,
      shouldFilterUntrustedWorkspacePlugins,
      shouldFilterBundledByAllowlist,
      normalizedConfig,
      rootConfig: params.config
    })
  });
}
function isProviderPluginEligibleForRuntimeOwnerActivation(params) {
  if (!(0, _bundledDEq7iy1i.b)({
    plugin: toManifestOwnerRecord(params.plugin),
    normalizedConfig: params.normalizedConfig
  })) return false;
  if (params.plugin.origin !== "workspace") return true;
  return (0, _bundledDEq7iy1i.v)({
    plugin: toManifestOwnerRecord(params.plugin),
    normalizedConfig: params.normalizedConfig,
    rootConfig: params.rootConfig
  });
}
function resolveActivatableProviderOwnerPluginIds(params) {
  return resolveProviderOwnerPluginIds({
    ...params,
    isEligible: (plugin, normalizedConfig) => isProviderPluginEligibleForRuntimeOwnerActivation({
      plugin,
      normalizedConfig,
      rootConfig: params.config
    })
  });
}
function resolveManifestRegistry(params) {
  if (params.manifestRegistry) return params.manifestRegistry;
  return (0, _manifestRegistryInstalled5Jxol4QJ.t)({
    index: params.registry ?? loadProviderRegistrySnapshot(params),
    config: params.config,
    workspaceDir: params.workspaceDir,
    env: params.env,
    includeDisabled: params.includeDisabled
  });
}
function stripModelProfileSuffix(value) {
  return (0, _modelRefProfileCtGPNXes.t)(value).model;
}
function splitExplicitModelRef(rawModel) {
  const trimmed = rawModel.trim();
  if (!trimmed) return null;
  const slash = trimmed.indexOf("/");
  if (slash === -1) {
    const modelId = stripModelProfileSuffix(trimmed);
    return modelId ? { modelId } : null;
  }
  const provider = (0, _providerIdDIRgKpoh.r)(trimmed.slice(0, slash));
  const modelId = stripModelProfileSuffix(trimmed.slice(slash + 1));
  if (!provider || !modelId) return null;
  return {
    provider,
    modelId
  };
}
function resolveModelSupportMatchKind(plugin, modelId) {
  const patterns = plugin.modelSupport?.modelPatterns ?? [];
  for (const patternSource of patterns) try {
    if (new RegExp(patternSource, "u").test(modelId)) return "pattern";
  } catch {
    continue;
  }
  const prefixes = plugin.modelSupport?.modelPrefixes ?? [];
  for (const prefix of prefixes) if (modelId.startsWith(prefix)) return "prefix";
}
function dedupeSortedPluginIds(values) {
  return [...new Set(values)].toSorted((left, right) => left.localeCompare(right));
}
function resolvePreferredManifestPluginIds(registry, matchedPluginIds) {
  if (matchedPluginIds.length === 0) return;
  const uniquePluginIds = dedupeSortedPluginIds(matchedPluginIds);
  if (uniquePluginIds.length <= 1) return uniquePluginIds;
  const nonBundledPluginIds = uniquePluginIds.filter((pluginId) => {
    return registry.plugins.find((entry) => entry.id === pluginId)?.origin !== "bundled";
  });
  if (nonBundledPluginIds.length === 1) return nonBundledPluginIds;
  if (nonBundledPluginIds.length > 1) return;
}
function resolveOwningPluginIdsForProvider(params) {
  const normalizedProvider = (0, _providerIdDIRgKpoh.r)(params.provider);
  if (!normalizedProvider) return;
  if (params.manifestRegistry) {
    const pluginIds = params.manifestRegistry.plugins.filter((plugin) => plugin.providers.some((providerId) => (0, _providerIdDIRgKpoh.r)(providerId) === normalizedProvider) || plugin.cliBackends.some((backendId) => (0, _providerIdDIRgKpoh.r)(backendId) === normalizedProvider)).map((plugin) => plugin.id);
    return pluginIds.length > 0 ? pluginIds : void 0;
  }
  const env = params.env ?? process.env;
  const deduped = dedupeSortedPluginIds([...(0, _pluginRegistryCutMFnk.c)({
    config: params.config,
    workspaceDir: params.workspaceDir,
    env,
    providerId: normalizedProvider,
    includeDisabled: true
  }), ...(0, _pluginRegistryCutMFnk.s)({
    config: params.config,
    workspaceDir: params.workspaceDir,
    env,
    contribution: "cliBackends",
    matches: (backendId) => (0, _providerIdDIRgKpoh.r)(backendId) === normalizedProvider,
    includeDisabled: true
  })]);
  return deduped.length > 0 ? deduped : void 0;
}
function resolveOwningPluginIdsForModelRef(params) {
  const parsed = splitExplicitModelRef(params.model);
  if (!parsed) return;
  if (parsed.provider) return resolveOwningPluginIdsForProvider({
    provider: parsed.provider,
    config: params.config,
    workspaceDir: params.workspaceDir,
    env: params.env,
    manifestRegistry: params.manifestRegistry
  });
  const manifestRegistry = resolveManifestRegistry({
    ...params,
    includeDisabled: true
  });
  const preferredPatternPluginIds = resolvePreferredManifestPluginIds(manifestRegistry, manifestRegistry.plugins.filter((plugin) => resolveModelSupportMatchKind(plugin, parsed.modelId) === "pattern").map((plugin) => plugin.id));
  if (preferredPatternPluginIds) return preferredPatternPluginIds;
  return resolvePreferredManifestPluginIds(manifestRegistry, manifestRegistry.plugins.filter((plugin) => resolveModelSupportMatchKind(plugin, parsed.modelId) === "prefix").map((plugin) => plugin.id));
}
function resolveOwningPluginIdsForModelRefs(params) {
  const registry = params.manifestRegistry ? void 0 : loadProviderRegistrySnapshot(params);
  const manifestRegistry = params.manifestRegistry;
  return dedupeSortedPluginIds(params.models.flatMap((model) => resolveOwningPluginIdsForModelRef({
    model,
    config: params.config,
    workspaceDir: params.workspaceDir,
    env: params.env,
    ...(manifestRegistry ? { manifestRegistry } : {}),
    ...(registry ? { registry } : {})
  }) ?? []));
}
function resolveCatalogHookProviderPluginIds(params) {
  const registry = loadProviderRegistrySnapshot(params);
  const providerSurfacePluginIds = resolveProviderSurfacePluginIdSet({
    ...params,
    registry
  });
  const normalizedConfig = (0, _pluginRegistryCutMFnk.r)(params.config?.plugins, registry);
  const enabledProviderPluginIds = listRegistryPluginIds(registry, (plugin) => providerSurfacePluginIds.has(plugin.pluginId) && resolveEffectiveRegistryPluginActivation({
    plugin,
    normalizedConfig,
    rootConfig: params.config
  }).activated);
  const bundledCompatPluginIds = resolveBundledProviderCompatPluginIds(params);
  return [...new Set([...enabledProviderPluginIds, ...bundledCompatPluginIds])].toSorted((left, right) => left.localeCompare(right));
}
//#endregion /* v9-9db4c508581f34e6 */
