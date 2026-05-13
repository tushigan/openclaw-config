"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = isTestDefaultMemorySlotDisabled;exports.c = void 0;exports.d = resolveMemorySlotDecision;exports.f = resolvePluginActivationState;exports.i = void 0;exports.l = resolveEffectivePluginActivationState;exports.n = createPluginActivationSource;exports.o = normalizePluginId;exports.s = exports.r = void 0;exports.t = applyTestPluginDefaults;exports.u = void 0;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _configNormalizationSharedDamsNnJD = require("./config-normalization-shared-DamsNnJD.js");
var _slotsCQkAb1S = require("./slots-CQk-Ab1S.js");
//#region src/plugins/config-state.ts
const BUILT_IN_PLUGIN_ALIAS_FALLBACKS = [
["openai-codex", "openai"],
["google-gemini-cli", "google"],
["minimax-portal", "minimax"],
["minimax-portal-auth", "minimax"]];

const BUILT_IN_PLUGIN_ALIAS_LOOKUP = new Map([...BUILT_IN_PLUGIN_ALIAS_FALLBACKS, ...BUILT_IN_PLUGIN_ALIAS_FALLBACKS.map(([, pluginId]) => [pluginId, pluginId])]);
function getBundledPluginAliasLookup() {
  const lookup = /* @__PURE__ */new Map();
  for (const [alias, pluginId] of BUILT_IN_PLUGIN_ALIAS_FALLBACKS) lookup.set(alias, pluginId);
  return lookup;
}
function normalizePluginIdWithLookup(id, getAliasLookup) {
  const trimmed = (0, _stringCoerceBje8XVt.c)(id) ?? "";
  const normalized = (0, _stringCoerceBje8XVt.s)(trimmed) ?? "";
  const builtInAlias = BUILT_IN_PLUGIN_ALIAS_LOOKUP.get(normalized);
  if (builtInAlias) return builtInAlias;
  return getAliasLookup().get(normalized) ?? trimmed;
}
function createScopedPluginIdNormalizer() {
  let lookup;
  return (id) => normalizePluginIdWithLookup(id, () => {
    lookup ??= getBundledPluginAliasLookup();
    return lookup;
  });
}
function normalizePluginId(id) {
  return normalizePluginIdWithLookup(id, getBundledPluginAliasLookup);
}
const normalizePluginsConfig = (config) => {
  return (0, _configNormalizationSharedDamsNnJD.i)(config, createScopedPluginIdNormalizer());
};exports.s = normalizePluginsConfig;
function createPluginActivationSource(params) {
  return {
    plugins: params.plugins ?? normalizePluginsConfig(params.config?.plugins),
    rootConfig: params.config
  };
}
const hasExplicitMemorySlot = (plugins) => Boolean(plugins?.slots && Object.prototype.hasOwnProperty.call(plugins.slots, "memory"));
const hasExplicitMemoryEntry = (plugins) => Boolean(plugins?.entries && Object.prototype.hasOwnProperty.call(plugins.entries, (0, _slotsCQkAb1S.n)("memory")));
const hasExplicitPluginConfig = (plugins) => (0, _configNormalizationSharedDamsNnJD.t)(plugins);exports.r = hasExplicitPluginConfig;
function applyTestPluginDefaults(cfg, env = process.env) {
  if (!env.VITEST) return cfg;
  const plugins = cfg.plugins;
  if (hasExplicitPluginConfig(plugins)) {
    if (hasExplicitMemorySlot(plugins) || hasExplicitMemoryEntry(plugins)) return cfg;
    return {
      ...cfg,
      plugins: {
        ...plugins,
        slots: {
          ...plugins?.slots,
          memory: "none"
        }
      }
    };
  }
  return {
    ...cfg,
    plugins: {
      ...plugins,
      enabled: false,
      slots: {
        ...plugins?.slots,
        memory: "none"
      }
    }
  };
}
function isTestDefaultMemorySlotDisabled(cfg, env = process.env) {
  if (!env.VITEST) return false;
  const plugins = cfg.plugins;
  if (hasExplicitMemorySlot(plugins) || hasExplicitMemoryEntry(plugins)) return false;
  return true;
}
function resolvePluginActivationState(params) {
  return (0, _configNormalizationSharedDamsNnJD.l)((0, _configNormalizationSharedDamsNnJD.c)({
    ...params,
    activationSource: params.activationSource ?? createPluginActivationSource({
      config: params.rootConfig,
      plugins: params.config
    }),
    allowBundledChannelExplicitBypassesAllowlist: true,
    isBundledChannelEnabledByChannelConfig
  }));
}
const resolveEnableState = exports.u = (0, _configNormalizationSharedDamsNnJD.o)(resolvePluginActivationState);
const isBundledChannelEnabledByChannelConfig = exports.i = _configNormalizationSharedDamsNnJD.r;
const resolveEffectiveEnableState = exports.c = (0, _configNormalizationSharedDamsNnJD.a)(resolveEffectivePluginActivationState);
function resolveEffectivePluginActivationState(params) {
  return resolvePluginActivationState(params);
}
function resolveMemorySlotDecision(params) {
  return (0, _configNormalizationSharedDamsNnJD.s)(params);
}
//#endregion /* v9-e36d83701c5757e1 */
