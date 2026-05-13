"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.$ = resolveProviderRuntimePlugin;exports.A = resolveProviderReasoningOutputModeWithPlugin;exports.B = resolveProviderWebSocketSessionPolicyWithPlugin;exports.C = resolveExternalAuthProfilesWithPlugins;exports.D = resolveProviderConfigApiKeyWithPlugin;exports.E = resolveProviderCacheTtlEligibility;exports.F = resolveProviderTextTransforms;exports.G = shouldPreferProviderRuntimeResolvedModel;exports.H = runProviderDynamicModel;exports.I = resolveProviderThinkingProfile;exports.J = resolveRuntimeTextTransforms;exports.K = transformProviderSystemPrompt;exports.L = resolveProviderTransportTurnStateWithPlugin;exports.M = resolveProviderStreamFn;exports.N = resolveProviderSyntheticAuthWithPlugin;exports.O = resolveProviderDefaultThinkingLevel;exports.P = resolveProviderSystemPromptContribution;exports.Q = resolveProviderFollowupFallbackRoute;exports.R = resolveProviderUsageAuthWithPlugin;exports.S = refreshProviderOAuthCredentialWithPlugin;exports.T = resolveProviderBinaryThinking;exports.U = sanitizeProviderReplayHistoryWithPlugin;exports.V = resolveProviderXHighThinking;exports.W = shouldDeferProviderSyntheticProfileAuthWithPlugin;exports.X = resolveProviderAuthProfileId;exports.Y = prepareProviderExtraParams;exports.Z = resolveProviderExtraParamsForTransport;exports._ = normalizeProviderResolvedModelWithPlugin;exports.a = applyProviderResolvedTransportWithPlugin;exports.b = prepareProviderDynamicModel;exports.c = buildProviderMissingAuthMessageWithPlugin;exports.d = createProviderEmbeddingProvider;exports.et = wrapProviderStreamFn;exports.f = formatProviderAuthProfileApiKeyWithPlugin;exports.g = normalizeProviderModelIdWithPlugin;exports.h = normalizeProviderConfigWithPlugin;exports.i = applyProviderResolvedModelCompatWithPlugins;exports.j = resolveProviderReplayPolicyWithPlugin;exports.k = resolveProviderModernModelRef;exports.l = buildProviderUnknownModelHintWithPlugin;exports.m = matchesProviderContextOverflowWithPlugin;exports.n = applyProviderConfigDefaultsWithPlugin;exports.o = augmentModelCatalogWithProviderPlugins;exports.p = inspectProviderToolSchemasWithPlugin;exports.q = validateProviderReplayTurnsWithPlugin;exports.r = applyProviderNativeStreamingUsageCompatWithPlugin;exports.s = buildProviderAuthDoctorHintWithPlugin;exports.t = void 0;exports.u = classifyProviderFailoverReasonWithPlugin;exports.v = normalizeProviderToolSchemasWithPlugin;exports.w = resolveExternalOAuthProfilesWithPlugins;exports.x = prepareProviderRuntimeAuth;exports.y = normalizeProviderTransportWithPlugin;exports.z = resolveProviderUsageSnapshotWithPlugin;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _ansiDqm1lzVL = require("./ansi-Dqm1lzVL.js");
var _pluginMetadataSnapshotMEvRUosy = require("./plugin-metadata-snapshot-mEvRUosy.js");
var _pluginCachePrimitivesWfwcOrBF = require("./plugin-cache-primitives-WfwcOrBF.js");
var _providerIdDIRgKpoh = require("./provider-id-DIRgKpoh.js");
var _subsystemCxWoQXRD = require("./subsystem-CxWoQXRD.js");
var _providerPublicArtifactsBto26nnC = require("./provider-public-artifacts-Bto26nnC.js");
var _runtimeStateNl5PFZKO = require("./runtime-state-Nl5PFZKO.js");
var _gpt5PromptOverlayBn1l8coq = require("./gpt5-prompt-overlay-Bn1l8coq.js");
var _pluginTextTransformsB2rjO5xY = require("./plugin-text-transforms-B2rjO5xY.js");
var _manifestModelIdNormalizationCBjIgmYG = require("./manifest-model-id-normalization-CBjIgmYG.js");
var _providersChCs1dXB = require("./providers-ChCs1dXB.js");
var _activeRuntimeRegistryDv4u8i3g = require("./active-runtime-registry-Dv4u8i3g.js");
var _providersRuntimeHbUzyUP = require("./providers.runtime-hb-uzyUP.js");
var _providerDiscoveryRuntime = require("./provider-discovery.runtime.js");
//#region src/plugins/provider-hook-runtime.ts
const providerRuntimePluginCache = /* @__PURE__ */new WeakMap();
function matchesProviderId(provider, providerId) {
  const normalized = (0, _providerIdDIRgKpoh.r)(providerId);
  if (!normalized) return false;
  if ((0, _providerIdDIRgKpoh.r)(provider.id) === normalized) return true;
  return [...(provider.aliases ?? []), ...(provider.hookAliases ?? [])].some((alias) => (0, _providerIdDIRgKpoh.r)(alias) === normalized);
}
function resolveProviderRuntimePluginCacheKey(params) {
  return JSON.stringify({
    provider: (0, _stringCoerceBje8XVt.a)(params.provider),
    pluginControlPlane: (0, _pluginMetadataSnapshotMEvRUosy.a)({
      config: params.config,
      env: params.env,
      workspaceDir: params.workspaceDir
    }),
    plugins: params.config?.plugins,
    models: params.config?.models?.providers,
    workspaceDir: params.workspaceDir ?? "",
    applyAutoEnable: params.applyAutoEnable ?? null,
    bundledProviderAllowlistCompat: params.bundledProviderAllowlistCompat ?? null,
    bundledProviderVitestCompat: params.bundledProviderVitestCompat ?? null
  });
}
function matchesProviderLiteralId(provider, providerId) {
  const normalized = (0, _stringCoerceBje8XVt.a)(providerId);
  return !!normalized && (0, _stringCoerceBje8XVt.a)(provider.id) === normalized;
}
function resolveCompatibleActiveProviderRegistry(params) {
  return (0, _activeRuntimeRegistryDv4u8i3g.n)({
    env: params.env,
    workspaceDir: params.workspaceDir
  });
}
function findProviderRuntimePluginInRegistry(params) {
  return params.registry.providers.map((entry) => Object.assign({}, entry.provider, { pluginId: entry.pluginId })).find((plugin) => {
    if (params.apiOwnerHint) return matchesProviderLiteralId(plugin, params.provider) || matchesProviderId(plugin, params.apiOwnerHint);
    return matchesProviderId(plugin, params.provider);
  });
}
function resolveProviderPluginsForHooks(params) {
  const env = params.env ?? process.env;
  const workspaceDir = params.workspaceDir ?? (0, _runtimeStateNl5PFZKO.n)();
  if ((0, _providersRuntimeHbUzyUP.t)({
    ...params,
    workspaceDir,
    env,
    activate: false,
    applyAutoEnable: params.applyAutoEnable,
    bundledProviderAllowlistCompat: params.bundledProviderAllowlistCompat ?? true,
    bundledProviderVitestCompat: params.bundledProviderVitestCompat ?? true
  })) return [];
  return (0, _providersRuntimeHbUzyUP.n)({
    ...params,
    workspaceDir,
    env,
    activate: false,
    applyAutoEnable: params.applyAutoEnable,
    bundledProviderAllowlistCompat: params.bundledProviderAllowlistCompat ?? true,
    bundledProviderVitestCompat: params.bundledProviderVitestCompat ?? true
  });
}
function resolveProviderRuntimePlugin(params) {
  const apiOwnerHint = (0, _providersRuntimeHbUzyUP.r)({
    provider: params.provider,
    config: params.config
  });
  const activeRegistry = resolveCompatibleActiveProviderRegistry(params);
  const activePlugin = activeRegistry ? findProviderRuntimePluginInRegistry({
    registry: activeRegistry,
    provider: params.provider,
    apiOwnerHint
  }) : void 0;
  if (activePlugin) return activePlugin;
  return (0, _pluginCachePrimitivesWfwcOrBF.i)({
    cache: providerRuntimePluginCache,
    config: params.env && params.env !== process.env ? void 0 : params.config,
    key: resolveProviderRuntimePluginCacheKey(params),
    load: () => {
      return resolveProviderPluginsForHooks({
        config: params.config,
        workspaceDir: params.workspaceDir ?? (0, _runtimeStateNl5PFZKO.n)(),
        env: params.env,
        providerRefs: apiOwnerHint ? [params.provider, apiOwnerHint] : [params.provider],
        applyAutoEnable: params.applyAutoEnable,
        bundledProviderAllowlistCompat: params.bundledProviderAllowlistCompat,
        bundledProviderVitestCompat: params.bundledProviderVitestCompat
      }).find((plugin) => {
        if (apiOwnerHint) return matchesProviderLiteralId(plugin, params.provider) || matchesProviderId(plugin, apiOwnerHint);
        return matchesProviderId(plugin, params.provider);
      }) ?? null;
    }
  }) ?? void 0;
}
function resolveProviderHookPlugin(params) {
  return resolveProviderRuntimePlugin(params) ?? resolveProviderPluginsForHooks({
    config: params.config,
    workspaceDir: params.workspaceDir,
    env: params.env
  }).find((candidate) => matchesProviderId(candidate, params.provider));
}
function prepareProviderExtraParams(params) {
  return resolveProviderRuntimePlugin(params)?.prepareExtraParams?.(params.context) ?? void 0;
}
function resolveProviderExtraParamsForTransport(params) {
  return resolveProviderRuntimePlugin(params)?.extraParamsForTransport?.(params.context) ?? void 0;
}
function resolveProviderAuthProfileId(params) {
  const resolved = resolveProviderRuntimePlugin(params)?.resolveAuthProfileId?.(params.context);
  return typeof resolved === "string" && resolved.trim() ? resolved.trim() : void 0;
}
function resolveProviderFollowupFallbackRoute(params) {
  return resolveProviderHookPlugin(params)?.followupFallbackRoute?.(params.context) ?? void 0;
}
function wrapProviderStreamFn(params) {
  return resolveProviderRuntimePlugin(params)?.wrapStreamFn?.(params.context) ?? void 0;
}
//#endregion
//#region src/plugins/text-transforms.runtime.ts
function resolveRuntimeTextTransforms() {
  const registry = (0, _activeRuntimeRegistryDv4u8i3g.t)();
  return (0, _pluginTextTransformsB2rjO5xY.n)(...(Array.isArray(registry?.textTransforms) ? registry.textTransforms.map((entry) => entry.transforms) : []));
}
//#endregion
//#region src/plugins/provider-runtime.ts
const log = (0, _subsystemCxWoQXRD.t)("plugins/provider-runtime");
const warnedExternalAuthFallbackPluginIds = /* @__PURE__ */new Set();
function matchesProviderPluginRef(provider, providerId) {
  const normalized = (0, _providerIdDIRgKpoh.r)(providerId);
  if (!normalized) return false;
  if ((0, _providerIdDIRgKpoh.r)(provider.id) === normalized) return true;
  return [...(provider.aliases ?? []), ...(provider.hookAliases ?? [])].some((alias) => (0, _providerIdDIRgKpoh.r)(alias) === normalized);
}
function resolveProviderHookRefs(provider, providerConfig) {
  const refs = [provider];
  const apiRef = (0, _stringCoerceBje8XVt.c)(providerConfig?.api);
  if (apiRef && (0, _providerIdDIRgKpoh.r)(apiRef) !== (0, _providerIdDIRgKpoh.r)(provider)) refs.push(apiRef);
  return [...new Set(refs)];
}
function matchesAnyProviderPluginRef(provider, providerRefs) {
  return providerRefs.some((providerRef) => matchesProviderPluginRef(provider, providerRef));
}
function hasExplicitProviderRuntimePluginActivation(params) {
  if (!params.config) return true;
  const ownerPluginIds = (0, _providersChCs1dXB.d)({
    provider: params.provider,
    config: params.config,
    workspaceDir: params.workspaceDir,
    env: params.env
  }) ?? [];
  if (ownerPluginIds.length === 0) return false;
  const allow = new Set(params.config.plugins?.allow ?? []);
  const entries = params.config.plugins?.entries ?? {};
  return ownerPluginIds.some((pluginId) => allow.has(pluginId) || entries[pluginId] !== void 0);
}
function resetExternalAuthFallbackWarningCacheForTest() {
  warnedExternalAuthFallbackPluginIds.clear();
}
const __testing = exports.t = { resetExternalAuthFallbackWarningCacheForTest };
function resolveProviderPluginsForCatalogHooks(params) {
  const workspaceDir = params.workspaceDir ?? (0, _runtimeStateNl5PFZKO.n)();
  const env = params.env ?? process.env;
  const onlyPluginIds = (0, _providersChCs1dXB.r)({
    config: params.config,
    workspaceDir,
    env
  });
  if (onlyPluginIds.length === 0) return [];
  return resolveProviderPluginsForHooks({
    ...params,
    workspaceDir,
    env,
    onlyPluginIds
  });
}
function runProviderDynamicModel(params) {
  return resolveProviderRuntimePlugin(params)?.resolveDynamicModel?.(params.context) ?? void 0;
}
function resolveProviderSystemPromptContribution(params) {
  const plugin = resolveProviderRuntimePlugin(params);
  const baseOverlay = (0, _gpt5PromptOverlayBn1l8coq.l)({
    config: params.context.config ?? params.config,
    providerId: params.context.provider ?? params.provider,
    modelId: params.context.modelId,
    trigger: params.context.trigger
  });
  return mergeProviderSystemPromptContributions(mergeProviderSystemPromptContributions(baseOverlay, plugin?.resolvePromptOverlay?.({
    ...params.context,
    baseOverlay
  }) ?? void 0), plugin?.resolveSystemPromptContribution?.(params.context) ?? void 0);
}
function mergeProviderSystemPromptContributions(base, override) {
  if (!base) return override;
  if (!override) return base;
  const stablePrefix = mergeUniquePromptSections(base.stablePrefix, override.stablePrefix);
  const dynamicSuffix = mergeUniquePromptSections(base.dynamicSuffix, override.dynamicSuffix);
  return {
    ...(stablePrefix ? { stablePrefix } : {}),
    ...(dynamicSuffix ? { dynamicSuffix } : {}),
    sectionOverrides: {
      ...base.sectionOverrides,
      ...override.sectionOverrides
    }
  };
}
function mergeUniquePromptSections(...sections) {
  const uniqueSections = [...new Set(sections.filter((section) => section?.trim()))];
  return uniqueSections.length > 0 ? uniqueSections.join("\n\n") : void 0;
}
function transformProviderSystemPrompt(params) {
  const plugin = resolveProviderRuntimePlugin(params);
  const textTransforms = (0, _pluginTextTransformsB2rjO5xY.n)(resolveRuntimeTextTransforms(), plugin?.textTransforms);
  return (0, _pluginTextTransformsB2rjO5xY.t)(plugin?.transformSystemPrompt?.(params.context) ?? params.context.systemPrompt, textTransforms?.input);
}
function resolveProviderTextTransforms(params) {
  return (0, _pluginTextTransformsB2rjO5xY.n)(resolveRuntimeTextTransforms(), resolveProviderRuntimePlugin(params)?.textTransforms);
}
async function prepareProviderDynamicModel(params) {
  await resolveProviderRuntimePlugin(params)?.prepareDynamicModel?.(params.context);
}
function shouldPreferProviderRuntimeResolvedModel(params) {
  return resolveProviderRuntimePlugin(params)?.preferRuntimeResolvedModel?.(params.context) ?? false;
}
function normalizeProviderResolvedModelWithPlugin(params) {
  return resolveProviderRuntimePlugin(params)?.normalizeResolvedModel?.(params.context) ?? void 0;
}
function resolveProviderCompatHookPlugins(params) {
  const candidates = resolveProviderPluginsForHooks(params);
  const owner = resolveProviderRuntimePlugin(params);
  if (!owner) return candidates;
  const ordered = [owner, ...candidates];
  const seen = /* @__PURE__ */new Set();
  return ordered.filter((candidate) => {
    const key = `${candidate.pluginId ?? ""}:${candidate.id}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
function applyCompatPatchToModel(model, patch) {
  const compat = model.compat && typeof model.compat === "object" ? model.compat : void 0;
  if (Object.entries(patch).every(([key, value]) => compat?.[key] === value)) return model;
  return {
    ...model,
    compat: {
      ...compat,
      ...patch
    }
  };
}
function applyProviderResolvedModelCompatWithPlugins(params) {
  let nextModel = params.context.model;
  let changed = false;
  for (const plugin of resolveProviderCompatHookPlugins(params)) {
    const patch = plugin.contributeResolvedModelCompat?.({
      ...params.context,
      model: nextModel
    });
    if (!patch || typeof patch !== "object") continue;
    const patchedModel = applyCompatPatchToModel(nextModel, patch);
    if (patchedModel === nextModel) continue;
    nextModel = patchedModel;
    changed = true;
  }
  return changed ? nextModel : void 0;
}
function applyProviderResolvedTransportWithPlugin(params) {
  const normalized = normalizeProviderTransportWithPlugin({
    provider: params.provider,
    config: params.config,
    workspaceDir: params.workspaceDir,
    env: params.env,
    context: {
      provider: params.context.provider,
      api: params.context.model.api,
      baseUrl: params.context.model.baseUrl
    }
  });
  if (!normalized) return;
  const nextApi = normalized.api ?? params.context.model.api;
  const nextBaseUrl = normalized.baseUrl ?? params.context.model.baseUrl;
  if (nextApi === params.context.model.api && nextBaseUrl === params.context.model.baseUrl) return;
  return {
    ...params.context.model,
    api: nextApi,
    baseUrl: nextBaseUrl
  };
}
function normalizeProviderModelIdWithPlugin(params) {
  return (0, _stringCoerceBje8XVt.c)(resolveProviderHookPlugin(params)?.normalizeModelId?.(params.context)) ?? (0, _manifestModelIdNormalizationCBjIgmYG.t)(params);
}
function normalizeProviderTransportWithPlugin(params) {
  const hasTransportChange = (normalized) => (normalized.api ?? params.context.api) !== params.context.api || (normalized.baseUrl ?? params.context.baseUrl) !== params.context.baseUrl;
  const matchedPlugin = resolveProviderHookPlugin(params);
  const normalizedMatched = matchedPlugin?.normalizeTransport?.(params.context);
  if (normalizedMatched && hasTransportChange(normalizedMatched)) return normalizedMatched;
  for (const candidate of resolveProviderPluginsForHooks(params)) {
    if (!candidate.normalizeTransport || candidate === matchedPlugin) continue;
    const normalized = candidate.normalizeTransport(params.context);
    if (normalized && hasTransportChange(normalized)) return normalized;
  }
}
function normalizeProviderConfigWithPlugin(params) {
  const hasConfigChange = (normalized) => normalized !== params.context.providerConfig;
  const bundledSurface = (0, _providerPublicArtifactsBto26nnC.t)(params.provider);
  if (bundledSurface?.normalizeConfig) {
    const normalized = bundledSurface.normalizeConfig(params.context);
    return normalized && hasConfigChange(normalized) ? normalized : void 0;
  }
  if (!hasExplicitProviderRuntimePluginActivation(params)) return;
  if (params.allowRuntimePluginLoad === false) return;
  const normalizedMatched = resolveProviderRuntimePlugin(params)?.normalizeConfig?.(params.context);
  return normalizedMatched && hasConfigChange(normalizedMatched) ? normalizedMatched : void 0;
}
function applyProviderNativeStreamingUsageCompatWithPlugin(params) {
  if (params.allowRuntimePluginLoad === false) return;
  return resolveProviderRuntimePlugin(params)?.applyNativeStreamingUsageCompat?.(params.context) ?? void 0;
}
function resolveProviderConfigApiKeyWithPlugin(params) {
  const bundledSurface = (0, _providerPublicArtifactsBto26nnC.t)(params.provider);
  if (bundledSurface?.resolveConfigApiKey) return (0, _stringCoerceBje8XVt.c)(bundledSurface.resolveConfigApiKey(params.context));
  if (params.allowRuntimePluginLoad === false) return;
  return (0, _stringCoerceBje8XVt.c)(resolveProviderRuntimePlugin(params)?.resolveConfigApiKey?.(params.context));
}
function resolveProviderReplayPolicyWithPlugin(params) {
  return resolveProviderRuntimePlugin(params)?.buildReplayPolicy?.(params.context) ?? void 0;
}
async function sanitizeProviderReplayHistoryWithPlugin(params) {
  return await resolveProviderRuntimePlugin(params)?.sanitizeReplayHistory?.(params.context);
}
async function validateProviderReplayTurnsWithPlugin(params) {
  return await resolveProviderRuntimePlugin(params)?.validateReplayTurns?.(params.context);
}
function normalizeProviderToolSchemasWithPlugin(params) {
  return resolveProviderRuntimePlugin(params)?.normalizeToolSchemas?.(params.context) ?? void 0;
}
function inspectProviderToolSchemasWithPlugin(params) {
  return resolveProviderRuntimePlugin(params)?.inspectToolSchemas?.(params.context) ?? void 0;
}
function resolveProviderReasoningOutputModeWithPlugin(params) {
  const mode = resolveProviderRuntimePlugin(params)?.resolveReasoningOutputMode?.(params.context);
  return mode === "native" || mode === "tagged" ? mode : void 0;
}
function resolveProviderStreamFn(params) {
  return resolveProviderRuntimePlugin(params)?.createStreamFn?.(params.context) ?? void 0;
}
function resolveProviderTransportTurnStateWithPlugin(params) {
  return resolveProviderRuntimePlugin(params)?.resolveTransportTurnState?.(params.context) ?? void 0;
}
function resolveProviderWebSocketSessionPolicyWithPlugin(params) {
  return resolveProviderRuntimePlugin(params)?.resolveWebSocketSessionPolicy?.(params.context) ?? void 0;
}
async function createProviderEmbeddingProvider(params) {
  return await resolveProviderRuntimePlugin(params)?.createEmbeddingProvider?.(params.context);
}
async function prepareProviderRuntimeAuth(params) {
  return await resolveProviderRuntimePlugin(params)?.prepareRuntimeAuth?.(params.context);
}
async function resolveProviderUsageAuthWithPlugin(params) {
  return await resolveProviderRuntimePlugin(params)?.resolveUsageAuth?.(params.context);
}
async function resolveProviderUsageSnapshotWithPlugin(params) {
  return await resolveProviderRuntimePlugin(params)?.fetchUsageSnapshot?.(params.context);
}
function matchesProviderContextOverflowWithPlugin(params) {
  const plugins = params.provider ? [resolveProviderHookPlugin({
    ...params,
    provider: params.provider
  })].filter((plugin) => Boolean(plugin)) : resolveProviderPluginsForHooks(params);
  for (const plugin of plugins) if (plugin.matchesContextOverflowError?.(params.context)) return true;
  return false;
}
function classifyProviderFailoverReasonWithPlugin(params) {
  const plugins = params.provider ? [resolveProviderHookPlugin({
    ...params,
    provider: params.provider
  })].filter((plugin) => Boolean(plugin)) : resolveProviderPluginsForHooks(params);
  for (const plugin of plugins) {
    const reason = plugin.classifyFailoverReason?.(params.context);
    if (reason) return reason;
  }
}
function formatProviderAuthProfileApiKeyWithPlugin(params) {
  return resolveProviderRuntimePlugin(params)?.formatApiKey?.(params.context);
}
async function refreshProviderOAuthCredentialWithPlugin(params) {
  return await resolveProviderRuntimePlugin(params)?.refreshOAuth?.(params.context);
}
async function buildProviderAuthDoctorHintWithPlugin(params) {
  return await resolveProviderRuntimePlugin(params)?.buildAuthDoctorHint?.(params.context);
}
function resolveProviderCacheTtlEligibility(params) {
  return resolveProviderRuntimePlugin(params)?.isCacheTtlEligible?.(params.context);
}
function resolveProviderBinaryThinking(params) {
  return resolveProviderRuntimePlugin(params)?.isBinaryThinking?.(params.context);
}
function resolveProviderXHighThinking(params) {
  return resolveProviderRuntimePlugin(params)?.supportsXHighThinking?.(params.context);
}
function resolveProviderThinkingProfile(params) {
  return resolveProviderRuntimePlugin(params)?.resolveThinkingProfile?.(params.context);
}
function resolveProviderDefaultThinkingLevel(params) {
  return resolveProviderRuntimePlugin(params)?.resolveDefaultThinkingLevel?.(params.context);
}
function applyProviderConfigDefaultsWithPlugin(params) {
  const bundledSurface = (0, _providerPublicArtifactsBto26nnC.t)(params.provider);
  if (bundledSurface?.applyConfigDefaults) return bundledSurface.applyConfigDefaults(params.context) ?? void 0;
  return resolveProviderRuntimePlugin(params)?.applyConfigDefaults?.(params.context) ?? void 0;
}
function resolveProviderModernModelRef(params) {
  return resolveProviderRuntimePlugin(params)?.isModernModelRef?.(params.context);
}
function buildProviderMissingAuthMessageWithPlugin(params) {
  return resolveProviderRuntimePlugin(params)?.buildMissingAuthMessage?.(params.context) ?? void 0;
}
function buildProviderUnknownModelHintWithPlugin(params) {
  return resolveProviderRuntimePlugin(params)?.buildUnknownModelHint?.(params.context) ?? void 0;
}
function resolveProviderSyntheticAuthWithPlugin(params) {
  const providerRefs = resolveProviderHookRefs(params.provider, params.context.providerConfig);
  const discoveryPluginIds = [...new Set(providerRefs.flatMap((provider) => (0, _providersChCs1dXB.d)({
    provider,
    config: params.config,
    workspaceDir: params.workspaceDir,
    env: params.env
  }) ?? []))];
  const discoveryProvider = (discoveryPluginIds.length > 0 ? (0, _providerDiscoveryRuntime.t)({
    config: params.config,
    workspaceDir: params.workspaceDir,
    env: params.env,
    onlyPluginIds: discoveryPluginIds,
    discoveryEntriesOnly: true
  }) : []).find((provider) => matchesAnyProviderPluginRef(provider, providerRefs));
  if (typeof discoveryProvider?.resolveSyntheticAuth === "function") return discoveryProvider.resolveSyntheticAuth(params.context) ?? void 0;
  const runtimeResolved = resolveProviderRuntimePlugin({
    ...params,
    applyAutoEnable: false,
    bundledProviderAllowlistCompat: false,
    bundledProviderVitestCompat: false
  })?.resolveSyntheticAuth?.(params.context);
  if (runtimeResolved) return runtimeResolved;
  for (const providerRef of providerRefs) {
    if ((0, _providerIdDIRgKpoh.r)(providerRef) === (0, _providerIdDIRgKpoh.r)(params.provider)) continue;
    const runtimeProviderResolved = resolveProviderRuntimePlugin({
      ...params,
      provider: providerRef,
      applyAutoEnable: false,
      bundledProviderAllowlistCompat: false,
      bundledProviderVitestCompat: false
    })?.resolveSyntheticAuth?.(params.context);
    if (runtimeProviderResolved) return runtimeProviderResolved;
  }
  if (providerRefs.length === 1) return (0, _providerDiscoveryRuntime.t)({
    config: params.config,
    workspaceDir: params.workspaceDir,
    env: params.env
  }).find((provider) => matchesAnyProviderPluginRef(provider, providerRefs))?.resolveSyntheticAuth?.(params.context);
}
function resolveExternalAuthProfilesWithPlugins(params) {
  const workspaceDir = params.workspaceDir ?? (0, _runtimeStateNl5PFZKO.n)();
  const env = params.env ?? process.env;
  const externalAuthPluginIds = (0, _providersChCs1dXB.c)({
    config: params.config,
    workspaceDir,
    env
  });
  const declaredPluginIds = new Set(externalAuthPluginIds);
  const fallbackPluginIds = (0, _providersChCs1dXB.s)({
    config: params.config,
    workspaceDir,
    env,
    declaredPluginIds
  });
  const pluginIds = [...new Set([...externalAuthPluginIds, ...fallbackPluginIds])].toSorted((left, right) => left.localeCompare(right));
  if (pluginIds.length === 0) return [];
  const matches = [];
  for (const plugin of resolveProviderPluginsForHooks({
    ...params,
    workspaceDir,
    env,
    onlyPluginIds: pluginIds
  })) {
    const profiles = plugin.resolveExternalAuthProfiles?.(params.context) ?? plugin.resolveExternalOAuthProfiles?.(params.context);
    if (!profiles || profiles.length === 0) continue;
    const pluginId = plugin.pluginId ?? plugin.id;
    if (!declaredPluginIds.has(pluginId) && !warnedExternalAuthFallbackPluginIds.has(pluginId)) {
      warnedExternalAuthFallbackPluginIds.add(pluginId);
      log.warn(`Provider plugin "${(0, _ansiDqm1lzVL.t)(pluginId)}" uses external auth hooks without declaring contracts.externalAuthProviders. This compatibility fallback is deprecated and will be removed in a future release.`);
    }
    matches.push(...profiles);
  }
  return matches;
}
function resolveExternalOAuthProfilesWithPlugins(params) {
  return resolveExternalAuthProfilesWithPlugins(params);
}
function shouldDeferProviderSyntheticProfileAuthWithPlugin(params) {
  const providerRefs = resolveProviderHookRefs(params.provider, params.context.providerConfig);
  for (const providerRef of providerRefs) {
    const resolved = resolveProviderRuntimePlugin({
      ...params,
      provider: providerRef
    })?.shouldDeferSyntheticProfileAuth?.(params.context);
    if (resolved !== void 0) return resolved;
  }
}
async function augmentModelCatalogWithProviderPlugins(params) {
  const supplemental = [];
  for (const plugin of resolveProviderPluginsForCatalogHooks(params)) {
    const next = await plugin.augmentModelCatalog?.(params.context);
    if (!next || next.length === 0) continue;
    supplemental.push(...next);
  }
  return supplemental;
}
//#endregion /* v9-34624dafdfd424e2 */
