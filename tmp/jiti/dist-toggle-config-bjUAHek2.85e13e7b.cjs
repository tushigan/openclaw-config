"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = setPluginEnabledInConfig;var _idsPHiL43bp = require("./ids-PHiL43bp.js");
//#region src/plugins/toggle-config.ts
function setPluginEnabledInConfig(config, pluginId, enabled, options = {}) {
  const builtInChannelId = (0, _idsPHiL43bp.r)(pluginId);
  const resolvedId = builtInChannelId ?? pluginId;
  const next = {
    ...config,
    plugins: {
      ...config.plugins,
      entries: {
        ...config.plugins?.entries,
        [resolvedId]: {
          ...config.plugins?.entries?.[resolvedId],
          enabled
        }
      }
    }
  };
  if (!builtInChannelId || options.updateChannelConfig === false) return next;
  const existing = config.channels?.[builtInChannelId];
  const existingRecord = existing && typeof existing === "object" && !Array.isArray(existing) ? existing : {};
  return {
    ...next,
    channels: {
      ...config.channels,
      [builtInChannelId]: {
        ...existingRecord,
        enabled
      }
    }
  };
}
//#endregion /* v9-af4a1ceb6f1afcf0 */
