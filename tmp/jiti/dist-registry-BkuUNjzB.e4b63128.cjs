"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = normalizeChannelId;exports.i = listChannelPlugins;exports.n = getLoadedChannelPlugin;exports.r = getLoadedChannelPluginOrigin;exports.t = getChannelPlugin;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _registryBy_qtZ6R = require("./registry-By_qtZ6R.js");
var _bundledDEq7iy1i = require("./bundled-DEq7iy1i.js");
var _registryLoadedChuwkhCQ = require("./registry-loaded-ChuwkhCQ.js");
//#region src/channels/plugins/registry.ts
function listChannelPlugins() {
  return (0, _registryLoadedChuwkhCQ.r)();
}
function getLoadedChannelPlugin(id) {
  const resolvedId = (0, _stringCoerceBje8XVt.c)(id) ?? "";
  if (!resolvedId) return;
  return (0, _registryLoadedChuwkhCQ.t)(resolvedId);
}
function getLoadedChannelPluginOrigin(id) {
  const resolvedId = (0, _stringCoerceBje8XVt.c)(id) ?? "";
  if (!resolvedId) return;
  return (0, _stringCoerceBje8XVt.c)((0, _registryLoadedChuwkhCQ.n)(resolvedId)?.origin) ?? void 0;
}
function getChannelPlugin(id) {
  const resolvedId = (0, _stringCoerceBje8XVt.c)(id) ?? "";
  if (!resolvedId) return;
  return getLoadedChannelPlugin(resolvedId) ?? (0, _bundledDEq7iy1i.n)(resolvedId);
}
function normalizeChannelId(raw) {
  return (0, _registryBy_qtZ6R.a)(raw);
}
//#endregion /* v9-5933ef22a2094b73 */
