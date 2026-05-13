"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = getLoadedChannelPluginForRead;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _runtimeChannelStateC_dvLbjP = require("./runtime-channel-state-C_dvLbjP.js");
//#region src/channels/plugins/registry-loaded-read.ts
function coerceLoadedChannelPlugin(plugin) {
  const id = (0, _stringCoerceBje8XVt.c)(plugin?.id) ?? "";
  if (!plugin || !id) return;
  if (!plugin.meta || typeof plugin.meta !== "object") plugin.meta = {};
  return plugin;
}
function getLoadedChannelPluginForRead(id) {
  const resolvedId = (0, _stringCoerceBje8XVt.c)(id) ?? "";
  if (!resolvedId) return;
  const registry = (0, _runtimeChannelStateC_dvLbjP.t)();
  if (!registry || !Array.isArray(registry.channels)) return;
  for (const entry of registry.channels) {
    const plugin = coerceLoadedChannelPlugin(entry?.plugin);
    if (plugin && plugin.id === resolvedId) return plugin;
  }
}
//#endregion /* v9-2b8188eb8381a440 */
