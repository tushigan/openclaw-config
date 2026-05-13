"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = withBundledPluginEnablementCompat;exports.r = withBundledPluginVitestCompat;exports.t = withBundledPluginAllowlistCompat;var _configStateWKtsQXM = require("./config-state-wKtsQXM5.js");
var _manifestRegistryBiAsJcRZ = require("./manifest-registry-BiAsJcRZ.js");
//#region src/plugins/bundled-compat.ts
function withBundledPluginAllowlistCompat(params) {
  if (params.config?.plugins?.bundledDiscovery !== "compat") return params.config;
  const allow = params.config?.plugins?.allow;
  if (!Array.isArray(allow) || allow.length === 0) return params.config;
  const allowSet = new Set(allow.map((entry) => entry.trim()).filter(Boolean));
  let changed = false;
  for (const pluginId of params.pluginIds) if (!allowSet.has(pluginId)) {
    allowSet.add(pluginId);
    changed = true;
  }
  if (!changed) return params.config;
  return {
    ...params.config,
    plugins: {
      ...params.config?.plugins,
      allow: [...allowSet]
    }
  };
}
function withBundledPluginEnablementCompat(params) {
  const existingEntries = params.config?.plugins?.entries ?? {};
  const forcePluginsEnabled = params.config?.plugins?.enabled === false;
  const useCompatDiscovery = params.config?.plugins?.bundledDiscovery === "compat";
  const allow = params.config?.plugins?.allow;
  const allowSet = !useCompatDiscovery && Array.isArray(allow) && allow.length > 0 ? new Set(allow.map((pluginId) => (0, _configStateWKtsQXM.o)(pluginId)).filter(Boolean)) : void 0;
  let hasEligiblePlugin = false;
  let changed = false;
  const nextEntries = { ...existingEntries };
  for (const pluginId of params.pluginIds) {
    if (allowSet && !allowSet.has(pluginId)) continue;
    hasEligiblePlugin = true;
    if (existingEntries[pluginId] !== void 0) continue;
    nextEntries[pluginId] = { enabled: true };
    changed = true;
  }
  if (!changed) {
    if (!forcePluginsEnabled || !hasEligiblePlugin) return params.config;
  }
  return {
    ...params.config,
    plugins: {
      ...params.config?.plugins,
      ...(forcePluginsEnabled ? { enabled: true } : {}),
      entries: {
        ...existingEntries,
        ...nextEntries
      }
    }
  };
}
function withBundledPluginVitestCompat(params) {
  const env = params.env ?? process.env;
  if (!Boolean(env.VITEST) || (0, _manifestRegistryBiAsJcRZ.n)(params.config?.plugins) || params.pluginIds.length === 0) return params.config;
  const entries = Object.fromEntries(params.pluginIds.map((pluginId) => [pluginId, { enabled: true }]));
  return {
    ...params.config,
    plugins: {
      ...params.config?.plugins,
      enabled: true,
      allow: [...params.pluginIds],
      entries: {
        ...entries,
        ...params.config?.plugins?.entries
      },
      slots: {
        ...params.config?.plugins?.slots,
        memory: "none"
      }
    }
  };
}
//#endregion /* v9-8692364cb37a9cb8 */
