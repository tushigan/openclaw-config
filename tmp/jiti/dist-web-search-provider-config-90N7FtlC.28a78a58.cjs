"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = setProviderWebSearchPluginConfigValue;exports.i = resolveProviderWebSearchPluginConfig;exports.n = getTopLevelCredentialValue;exports.o = setScopedCredentialValue;exports.r = mergeScopedSearchConfig;exports.s = setTopLevelCredentialValue;exports.t = getScopedCredentialValue;var _pluginWebSearchConfigD0yKjCnh = require("./plugin-web-search-config-D0yKjCnh.js");
//#region src/agents/tools/web-search-provider-config.ts
function getTopLevelCredentialValue(searchConfig) {
  return searchConfig?.apiKey;
}
function setTopLevelCredentialValue(searchConfigTarget, value) {
  searchConfigTarget.apiKey = value;
}
function getScopedCredentialValue(searchConfig, key) {
  const scoped = searchConfig?.[key];
  if (!scoped || typeof scoped !== "object" || Array.isArray(scoped)) return;
  return scoped.apiKey;
}
function setScopedCredentialValue(searchConfigTarget, key, value) {
  const scoped = searchConfigTarget[key];
  if (!scoped || typeof scoped !== "object" || Array.isArray(scoped)) {
    searchConfigTarget[key] = { apiKey: value };
    return;
  }
  scoped.apiKey = value;
}
function mergeScopedSearchConfig(searchConfig, key, pluginConfig, options) {
  if (!pluginConfig) return searchConfig;
  const currentScoped = searchConfig?.[key] && typeof searchConfig[key] === "object" && !Array.isArray(searchConfig[key]) ? searchConfig[key] : {};
  const next = {
    ...searchConfig,
    [key]: {
      ...currentScoped,
      ...pluginConfig
    }
  };
  if (options?.mirrorApiKeyToTopLevel && pluginConfig.apiKey !== void 0) next.apiKey = pluginConfig.apiKey;
  return next;
}
function resolveProviderWebSearchPluginConfig(config, pluginId) {
  return (0, _pluginWebSearchConfigD0yKjCnh.t)(config, pluginId);
}
function ensureObject(target, key) {
  const current = target[key];
  if (current && typeof current === "object" && !Array.isArray(current)) return current;
  const next = {};
  target[key] = next;
  return next;
}
function setProviderWebSearchPluginConfigValue(configTarget, pluginId, key, value) {
  const entry = ensureObject(ensureObject(ensureObject(configTarget, "plugins"), "entries"), pluginId);
  if (entry.enabled === void 0) entry.enabled = true;
  const webSearch = ensureObject(ensureObject(entry, "config"), "webSearch");
  webSearch[key] = value;
}
//#endregion /* v9-42be81b2f6d0ea85 */
