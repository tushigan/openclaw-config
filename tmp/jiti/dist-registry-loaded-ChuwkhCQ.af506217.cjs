"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = getLoadedChannelPluginEntryById;exports.r = listLoadedChannelPlugins;exports.t = getLoadedChannelPluginById;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _idsPHiL43bp = require("./ids-PHiL43bp.js");
var _runtimeChannelStateC_dvLbjP = require("./runtime-channel-state-C_dvLbjP.js");
require("./registry-By_qtZ6R.js");
//#region src/channels/plugins/registry-loaded.ts
function coerceLoadedChannelPlugin(plugin) {
  const id = (0, _stringCoerceBje8XVt.c)(plugin?.id) ?? "";
  if (!plugin || !id) return null;
  if (!plugin.meta || typeof plugin.meta !== "object") plugin.meta = {};
  return plugin;
}
function dedupeChannels(channels) {
  const seen = /* @__PURE__ */new Set();
  const resolved = [];
  for (const plugin of channels) {
    const id = (0, _stringCoerceBje8XVt.c)(plugin.id) ?? "";
    if (!id || seen.has(id)) continue;
    seen.add(id);
    resolved.push(plugin);
  }
  return resolved;
}
function resolveChannelPlugins() {
  const registry = (0, _runtimeChannelStateC_dvLbjP.t)();
  const channelPlugins = [];
  const pluginEntries = [];
  if (registry && Array.isArray(registry.channels)) for (const entry of registry.channels) {
    const plugin = coerceLoadedChannelPlugin(entry?.plugin);
    if (plugin) {
      channelPlugins.push(plugin);
      pluginEntries.push({
        ...entry,
        plugin
      });
    }
  }
  const sorted = dedupeChannels(channelPlugins).toSorted((a, b) => {
    const indexA = _idsPHiL43bp.n.indexOf(a.id);
    const indexB = _idsPHiL43bp.n.indexOf(b.id);
    const orderA = a.meta.order ?? (indexA === -1 ? 999 : indexA);
    const orderB = b.meta.order ?? (indexB === -1 ? 999 : indexB);
    if (orderA !== orderB) return orderA - orderB;
    return a.id.localeCompare(b.id);
  });
  const byId = /* @__PURE__ */new Map();
  const entriesById = /* @__PURE__ */new Map();
  const unsortedEntriesById = new Map(pluginEntries.map((entry) => [entry.plugin.id, entry]));
  for (const plugin of sorted) {
    byId.set(plugin.id, plugin);
    const entry = unsortedEntriesById.get(plugin.id);
    if (entry) entriesById.set(plugin.id, entry);
  }
  return {
    sorted,
    byId,
    entriesById
  };
}
function listLoadedChannelPlugins() {
  return resolveChannelPlugins().sorted.slice();
}
function getLoadedChannelPluginById(id) {
  const resolvedId = (0, _stringCoerceBje8XVt.c)(id) ?? "";
  if (!resolvedId) return;
  return resolveChannelPlugins().byId.get(resolvedId);
}
function getLoadedChannelPluginEntryById(id) {
  const resolvedId = (0, _stringCoerceBje8XVt.c)(id) ?? "";
  if (!resolvedId) return;
  return resolveChannelPlugins().entriesById.get(resolvedId);
}
//#endregion /* v9-b4613fdca08876e3 */
