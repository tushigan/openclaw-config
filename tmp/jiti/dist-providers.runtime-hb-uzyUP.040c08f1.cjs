"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolvePluginProviders;exports.r = resolveProviderConfigApiOwnerHint;exports.t = isPluginProvidersLoadInFlight;var _providerIdDIRgKpoh = require("./provider-id-DIRgKpoh.js");
var _packageStateProbesAnoN2cCB = require("./package-state-probes-AnoN2cCB.js");
var _providersChCs1dXB = require("./providers-ChCs1dXB.js");
var _activationContextB4dHEVKf = require("./activation-context-B4dHEVKf.js");
var _activationPlannerCzw78AnN = require("./activation-planner-Czw78AnN.js");
var _loaderBGXgDrk = require("./loader-B-GXgDrk.js");
var _runtimeB0MMVyKh = require("./runtime-B0MMVyKh.js");
var _activeRuntimeRegistryDv4u8i3g = require("./active-runtime-registry-Dv4u8i3g.js");
var _loadContextF7nKv0Wc = require("./load-context-f7nKv0Wc.js");
//#region src/plugins/provider-config-owner.ts
function resolveProviderConfigApiOwnerHint(params) {
  const providers = params.config?.models?.providers;
  if (!providers) return;
  const normalizedProvider = (0, _providerIdDIRgKpoh.r)(params.provider);
  if (!normalizedProvider) return;
  const providerConfig = providers[params.provider] ?? Object.entries(providers).find(([candidateId]) => (0, _providerIdDIRgKpoh.r)(candidateId) === normalizedProvider)?.[1];
  const api = typeof providerConfig?.api === "string" ? (0, _providerIdDIRgKpoh.r)(providerConfig.api) : "";
  if (!api || api === normalizedProvider) return;
  return api;
}
//#endregion
//#region src/plugins/providers.runtime.ts
function dedupeSortedPluginIds(values) {
  return [...new Set(values)].toSorted((left, right) => left.localeCompare(right));
}
function resolveExplicitProviderOwnerPluginIds(params) {
  return dedupeSortedPluginIds(params.providerRefs.flatMap((provider) => {
    const plannedPluginIds = (0, _activationPlannerCzw78AnN.t)({
      trigger: {
        kind: "provider",
        provider
      },
      config: params.config,
      workspaceDir: params.workspaceDir,
      env: params.env
    });
    if (plannedPluginIds.length > 0) return plannedPluginIds;
    const apiOwnerHint = resolveProviderConfigApiOwnerHint({
      provider,
      config: params.config
    });
    if (apiOwnerHint) {
      const apiOwnerPluginIds = (0, _activationPlannerCzw78AnN.t)({
        trigger: {
          kind: "provider",
          provider: apiOwnerHint
        },
        config: params.config,
        workspaceDir: params.workspaceDir,
        env: params.env
      });
      if (apiOwnerPluginIds.length > 0) return apiOwnerPluginIds;
      const legacyApiOwnerPluginIds = (0, _providersChCs1dXB.d)({
        provider: apiOwnerHint,
        config: params.config,
        workspaceDir: params.workspaceDir,
        env: params.env
      });
      if (legacyApiOwnerPluginIds?.length) return legacyApiOwnerPluginIds;
    }
    return (0, _providersChCs1dXB.d)({
      provider,
      config: params.config,
      workspaceDir: params.workspaceDir,
      env: params.env
    }) ?? [];
  }));
}
function mergeExplicitOwnerPluginIds(providerPluginIds, explicitOwnerPluginIds) {
  if (explicitOwnerPluginIds.length === 0) return [...providerPluginIds];
  return dedupeSortedPluginIds([...providerPluginIds, ...explicitOwnerPluginIds]);
}
function resolvePluginProviderLoadBase(params) {
  const env = params.env ?? process.env;
  const workspaceDir = params.workspaceDir ?? (0, _runtimeB0MMVyKh.c)();
  const providerOwnedPluginIds = params.providerRefs?.length ? resolveExplicitProviderOwnerPluginIds({
    providerRefs: params.providerRefs,
    config: params.config,
    workspaceDir,
    env
  }) : [];
  const modelOwnedPluginIds = params.modelRefs?.length ? (0, _providersChCs1dXB.u)({
    models: params.modelRefs,
    config: params.config,
    workspaceDir,
    env
  }) : [];
  return {
    env,
    workspaceDir,
    requestedPluginIds: (0, _packageStateProbesAnoN2cCB.i)(params.onlyPluginIds) || params.providerRefs?.length || params.modelRefs?.length || providerOwnedPluginIds.length > 0 || modelOwnedPluginIds.length > 0 ? [...new Set([
    ...(params.onlyPluginIds ?? []),
    ...providerOwnedPluginIds,
    ...modelOwnedPluginIds]
    )].toSorted((left, right) => left.localeCompare(right)) : void 0,
    explicitOwnerPluginIds: dedupeSortedPluginIds([...providerOwnedPluginIds, ...modelOwnedPluginIds]),
    rawConfig: params.config
  };
}
function resolveSetupProviderPluginLoadState(params, base) {
  const setupPluginIds = mergeExplicitOwnerPluginIds((0, _providersChCs1dXB.a)({
    config: params.config,
    workspaceDir: base.workspaceDir,
    env: base.env,
    onlyPluginIds: base.requestedPluginIds,
    includeUntrustedWorkspacePlugins: params.includeUntrustedWorkspacePlugins
  }), (0, _providersChCs1dXB.i)({
    pluginIds: base.explicitOwnerPluginIds,
    config: params.config,
    workspaceDir: base.workspaceDir,
    env: base.env,
    includeUntrustedWorkspacePlugins: params.includeUntrustedWorkspacePlugins
  }));
  if (setupPluginIds.length === 0) return;
  const setupConfig = (0, _activationContextB4dHEVKf.r)({
    config: base.rawConfig,
    pluginIds: setupPluginIds
  });
  return { loadOptions: (0, _loadContextF7nKv0Wc.n)({
      config: setupConfig,
      activationSourceConfig: setupConfig,
      autoEnabledReasons: {},
      workspaceDir: base.workspaceDir,
      env: base.env,
      logger: (0, _loadContextF7nKv0Wc.r)()
    }, {
      onlyPluginIds: setupPluginIds,
      pluginSdkResolution: params.pluginSdkResolution,
      cache: params.cache ?? false,
      activate: params.activate ?? false
    }) };
}
function resolveRuntimeProviderPluginLoadState(params, base) {
  const explicitOwnerPluginIds = (0, _providersChCs1dXB.t)({
    pluginIds: base.explicitOwnerPluginIds,
    config: base.rawConfig,
    workspaceDir: base.workspaceDir,
    env: base.env,
    includeUntrustedWorkspacePlugins: params.includeUntrustedWorkspacePlugins
  });
  const runtimeRequestedPluginIds = base.requestedPluginIds !== void 0 ? dedupeSortedPluginIds([...(params.onlyPluginIds ?? []), ...explicitOwnerPluginIds]) : void 0;
  const activation = (0, _activationContextB4dHEVKf.t)({
    rawConfig: (0, _activationContextB4dHEVKf.r)({
      config: base.rawConfig,
      pluginIds: explicitOwnerPluginIds
    }),
    env: base.env,
    workspaceDir: base.workspaceDir,
    onlyPluginIds: runtimeRequestedPluginIds,
    applyAutoEnable: params.applyAutoEnable ?? true,
    compatMode: {
      allowlist: params.bundledProviderAllowlistCompat,
      enablement: "allowlist",
      vitest: params.bundledProviderVitestCompat
    },
    resolveCompatPluginIds: _providersChCs1dXB.n
  });
  const config = params.bundledProviderVitestCompat ? (0, _providersChCs1dXB.f)({
    config: activation.config,
    pluginIds: activation.compatPluginIds,
    env: base.env
  }) : activation.config;
  const providerPluginIds = mergeExplicitOwnerPluginIds((0, _providersChCs1dXB.o)({
    config,
    workspaceDir: base.workspaceDir,
    env: base.env,
    onlyPluginIds: runtimeRequestedPluginIds
  }), explicitOwnerPluginIds);
  return { loadOptions: (0, _loadContextF7nKv0Wc.n)({
      config,
      activationSourceConfig: activation.activationSourceConfig,
      autoEnabledReasons: activation.autoEnabledReasons,
      workspaceDir: base.workspaceDir,
      env: base.env,
      logger: (0, _loadContextF7nKv0Wc.r)()
    }, {
      onlyPluginIds: providerPluginIds,
      pluginSdkResolution: params.pluginSdkResolution,
      cache: params.cache ?? true,
      activate: params.activate ?? false
    }) };
}
function isPluginProvidersLoadInFlight(params) {
  const base = resolvePluginProviderLoadBase(params);
  const loadState = params.mode === "setup" ? resolveSetupProviderPluginLoadState(params, base) : resolveRuntimeProviderPluginLoadState(params, base);
  if (!loadState) return false;
  return (0, _loaderBGXgDrk.s)(loadState.loadOptions);
}
function resolvePluginProviders(params) {
  const base = resolvePluginProviderLoadBase(params);
  if (params.mode === "setup") {
    const loadState = resolveSetupProviderPluginLoadState(params, base);
    if (!loadState) return [];
    return (0, _loaderBGXgDrk.l)(loadState.loadOptions).providers.map((entry) => Object.assign({}, entry.provider, { pluginId: entry.pluginId }));
  }
  const loadState = resolveRuntimeProviderPluginLoadState(params, base);
  const registry = loadState.loadOptions.onlyPluginIds?.length === 0 ? void 0 : (0, _activeRuntimeRegistryDv4u8i3g.n)({
    env: base.env,
    loadOptions: loadState.loadOptions,
    workspaceDir: base.workspaceDir,
    requiredPluginIds: loadState.loadOptions.onlyPluginIds
  }) ?? (0, _loaderBGXgDrk.o)(loadState.loadOptions);
  if (!registry) return [];
  return registry.providers.map((entry) => Object.assign({}, entry.provider, { pluginId: entry.pluginId }));
}
//#endregion /* v9-e3ee5287af50ed76 */
