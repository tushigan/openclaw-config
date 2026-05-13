"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = enablePluginInConfig;var _idsPHiL43bp = require("./ids-PHiL43bp.js");
var _toggleConfigBjUAHek = require("./toggle-config-bjUAHek2.js");
//#region src/plugins/enable.ts
function enablePluginInConfig(cfg, pluginId, options = {}) {
  const resolvedId = (0, _idsPHiL43bp.r)(pluginId) ?? pluginId;
  if (cfg.plugins?.enabled === false) return {
    config: cfg,
    enabled: false,
    pluginId: resolvedId,
    reason: "plugins disabled"
  };
  if (cfg.plugins?.deny?.includes(pluginId) || cfg.plugins?.deny?.includes(resolvedId)) return {
    config: cfg,
    enabled: false,
    pluginId: resolvedId,
    reason: "blocked by denylist"
  };
  const allow = cfg.plugins?.allow;
  if (Array.isArray(allow) && allow.length > 0 && !allow.includes(pluginId) && !allow.includes(resolvedId)) return {
    config: cfg,
    enabled: false,
    pluginId: resolvedId,
    reason: "blocked by allowlist"
  };
  return {
    config: (0, _toggleConfigBjUAHek.t)(cfg, resolvedId, true, options),
    enabled: true,
    pluginId: resolvedId
  };
}
//#endregion /* v9-42977eca6e54553e */
