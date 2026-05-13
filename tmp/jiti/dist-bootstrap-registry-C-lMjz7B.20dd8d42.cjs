"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = listBundledChannelIds;exports.n = getBootstrapChannelSecrets;exports.r = iterateBootstrapChannelPlugins;exports.t = getBootstrapChannelPlugin;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _channelCatalogRegistryCNXtcf4Q = require("./channel-catalog-registry-CNXtcf4Q.js");
var _bundledDEq7iy1i = require("./bundled-DEq7iy1i.js");
//#region src/channels/plugins/bundled-ids.ts
function listBundledChannelPluginIdsForRoot(_packageRoot, env = process.env) {
  return (0, _channelCatalogRegistryCNXtcf4Q.t)({
    origin: "bundled",
    env
  }).map((entry) => entry.pluginId).toSorted((left, right) => left.localeCompare(right));
}
function listBundledChannelIdsForRoot(_packageRoot, env = process.env) {
  return (0, _channelCatalogRegistryCNXtcf4Q.t)({
    origin: "bundled",
    env
  }).map((entry) => entry.channel.id).filter((channelId) => Boolean(channelId)).toSorted((left, right) => left.localeCompare(right));
}
function listBundledChannelIds(env = process.env) {
  return listBundledChannelIdsForRoot((0, _bundledDEq7iy1i.m)(env).cacheKey, env);
}
//#endregion
//#region src/channels/plugins/bootstrap-registry.ts
function resolveBootstrapChannelId(id) {
  return (0, _stringCoerceBje8XVt.c)(id) ?? "";
}
function mergePluginSection(runtimeValue, setupValue) {
  if (runtimeValue && setupValue && typeof runtimeValue === "object" && typeof setupValue === "object") {
    const merged = { ...runtimeValue };
    for (const [key, value] of Object.entries(setupValue)) if (value !== void 0) merged[key] = value;
    return { ...merged };
  }
  return setupValue ?? runtimeValue;
}
function mergeBootstrapPlugin(runtimePlugin, setupPlugin) {
  return {
    ...runtimePlugin,
    ...setupPlugin,
    meta: mergePluginSection(runtimePlugin.meta, setupPlugin.meta),
    capabilities: mergePluginSection(runtimePlugin.capabilities, setupPlugin.capabilities),
    commands: mergePluginSection(runtimePlugin.commands, setupPlugin.commands),
    doctor: mergePluginSection(runtimePlugin.doctor, setupPlugin.doctor),
    reload: mergePluginSection(runtimePlugin.reload, setupPlugin.reload),
    config: mergePluginSection(runtimePlugin.config, setupPlugin.config),
    setup: mergePluginSection(runtimePlugin.setup, setupPlugin.setup),
    messaging: mergePluginSection(runtimePlugin.messaging, setupPlugin.messaging),
    actions: mergePluginSection(runtimePlugin.actions, setupPlugin.actions),
    secrets: mergePluginSection(runtimePlugin.secrets, setupPlugin.secrets)
  };
}
function listBootstrapChannelPluginIds() {
  return listBundledChannelPluginIdsForRoot((0, _bundledDEq7iy1i.m)().cacheKey);
}
function* iterateBootstrapChannelPlugins() {
  for (const id of listBootstrapChannelPluginIds()) {
    const plugin = getBootstrapChannelPlugin(id);
    if (plugin) yield plugin;
  }
}
function getBootstrapChannelPlugin(id) {
  const resolvedId = resolveBootstrapChannelId(id);
  if (!resolvedId) return;
  let runtimePlugin;
  let setupPlugin;
  try {
    runtimePlugin = (0, _bundledDEq7iy1i.n)(resolvedId);
    setupPlugin = (0, _bundledDEq7iy1i.i)(resolvedId);
  } catch {
    return;
  }
  return runtimePlugin && setupPlugin ? mergeBootstrapPlugin(runtimePlugin, setupPlugin) : setupPlugin ?? runtimePlugin;
}
function getBootstrapChannelSecrets(id) {
  const resolvedId = resolveBootstrapChannelId(id);
  if (!resolvedId) return;
  try {
    return mergePluginSection((0, _bundledDEq7iy1i.r)(resolvedId), (0, _bundledDEq7iy1i.a)(resolvedId));
  } catch {
    return;
  }
}
//#endregion /* v9-dbdfb3436ae720b0 */
