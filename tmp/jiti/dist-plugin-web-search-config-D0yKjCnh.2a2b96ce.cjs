"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = resolvePluginWebSearchConfig; //#region src/config/plugin-web-search-config.ts
function isRecord(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function resolvePluginWebSearchConfig(config, pluginId) {
  const pluginConfig = config?.plugins?.entries?.[pluginId]?.config;
  if (!isRecord(pluginConfig)) return;
  return isRecord(pluginConfig.webSearch) ? pluginConfig.webSearch : void 0;
}
//#endregion /* v9-76b1048767a56b33 */
