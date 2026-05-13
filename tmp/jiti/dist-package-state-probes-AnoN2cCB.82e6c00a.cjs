"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = hasNonEmptyPluginIdScope;exports.i = hasExplicitPluginIdScope;exports.n = listBundledChannelIdsForPackageState;exports.o = normalizePluginIdScope;exports.r = createPluginIdScopeSet;exports.s = serializePluginIdScope;exports.t = hasBundledChannelPackageState;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _errorsQN8rySzW = require("./errors-QN8rySzW.js");
var _channelCatalogRegistryCNXtcf4Q = require("./channel-catalog-registry-CNXtcf4Q.js");
var _pluginModuleLoaderCacheB600Kx = require("./plugin-module-loader-cache-B60-0Kx3.js");
var _subsystemCxWoQXRD = require("./subsystem-CxWoQXRD.js");
var _bundledDEq7iy1i = require("./bundled-DEq7iy1i.js");
//#region src/plugins/plugin-scope.ts
function normalizePluginIdScope(ids) {
  if (ids === void 0) return;
  return Array.from(new Set(ids.filter((id) => typeof id === "string").map((id) => id.trim()).filter(Boolean))).toSorted();
}
function hasExplicitPluginIdScope(ids) {
  return ids !== void 0;
}
function hasNonEmptyPluginIdScope(ids) {
  return ids !== void 0 && ids.length > 0;
}
function createPluginIdScopeSet(ids) {
  if (ids === void 0) return null;
  return new Set(ids);
}
function serializePluginIdScope(ids) {
  return ids === void 0 ? "__unscoped__" : JSON.stringify(ids);
}
//#endregion
//#region src/channels/plugins/package-state-probes.ts
const log = (0, _subsystemCxWoQXRD.t)("channels");
const sourcePackageStateLoaderCache = /* @__PURE__ */new Map();
function isSourceModulePath(modulePath) {
  return /\.(?:c|m)?tsx?$/iu.test(modulePath);
}
function loadChannelPackageStateModule(params) {
  try {
    return (0, _bundledDEq7iy1i.h)(params);
  } catch (error) {
    if (!isSourceModulePath(params.modulePath)) throw error;
    return (0, _pluginModuleLoaderCacheB600Kx.n)({
      cache: sourcePackageStateLoaderCache,
      modulePath: params.modulePath,
      importerUrl: "file:///opt/homebrew/lib/node_modules/openclaw/dist/package-state-probes-AnoN2cCB.js",
      tryNative: true,
      cacheScopeKey: "channel-package-state"
    })(params.modulePath);
  }
}
function normalizeStringList(value) {
  if (!Array.isArray(value)) return [];
  return value.map((entry) => (0, _stringCoerceBje8XVt.c)(entry)).filter((entry) => Boolean(entry));
}
function hasNonEmptyEnvValue(env, key) {
  return typeof env?.[key] === "string" && env[key].trim().length > 0;
}
function resolveChannelPackageStateMetadata(entry, metadataKey) {
  const metadata = entry.channel[metadataKey];
  if (!metadata || typeof metadata !== "object") return null;
  const specifier = (0, _stringCoerceBje8XVt.c)(metadata.specifier) ?? "";
  const exportName = (0, _stringCoerceBje8XVt.c)(metadata.exportName) ?? "";
  const envMetadata = "env" in metadata ? metadata.env : void 0;
  const allOf = normalizeStringList(envMetadata?.allOf);
  const anyOf = normalizeStringList(envMetadata?.anyOf);
  const env = allOf.length > 0 || anyOf.length > 0 ? {
    allOf,
    anyOf
  } : void 0;
  if ((!specifier || !exportName) && !env) return null;
  return {
    ...(specifier ? { specifier } : {}),
    ...(exportName ? { exportName } : {}),
    ...(env ? { env } : {})
  };
}
function listChannelPackageStateCatalog(metadataKey) {
  return (0, _channelCatalogRegistryCNXtcf4Q.t)({ origin: "bundled" }).filter((entry) => Boolean(resolveChannelPackageStateMetadata(entry, metadataKey)));
}
function resolveChannelPackageStateChecker(params) {
  const metadata = resolveChannelPackageStateMetadata(params.entry, params.metadataKey);
  if (!metadata) return null;
  if (metadata.env) return ({ env }) => {
    const allOf = metadata.env?.allOf ?? [];
    const anyOf = metadata.env?.anyOf ?? [];
    return allOf.every((key) => hasNonEmptyEnvValue(env, key)) && (anyOf.length === 0 || anyOf.some((key) => hasNonEmptyEnvValue(env, key)));
  };
  try {
    const checker = loadChannelPackageStateModule({
      modulePath: (0, _bundledDEq7iy1i.g)(params.entry.rootDir, metadata.specifier),
      rootDir: params.entry.rootDir
    })[metadata.exportName];
    if (typeof checker !== "function") throw new Error(`missing ${params.metadataKey} export ${metadata.exportName}`);
    return checker;
  } catch (error) {
    const detail = (0, _errorsQN8rySzW.i)(error);
    log.warn(`[channels] failed to load ${params.metadataKey} checker for ${params.entry.pluginId}: ${detail}`);
    return null;
  }
}
function resolvePackageStateChannelId(entry) {
  return (0, _stringCoerceBje8XVt.c)(entry.channel.id);
}
function listBundledChannelIdsForPackageState(metadataKey) {
  return listChannelPackageStateCatalog(metadataKey).map((entry) => resolvePackageStateChannelId(entry)).filter((channelId) => Boolean(channelId));
}
function hasBundledChannelPackageState(params) {
  const requestedChannelId = (0, _stringCoerceBje8XVt.c)(params.channelId);
  const entry = listChannelPackageStateCatalog(params.metadataKey).find((candidate) => resolvePackageStateChannelId(candidate) === requestedChannelId);
  if (!entry) return false;
  const checker = resolveChannelPackageStateChecker({
    entry,
    metadataKey: params.metadataKey
  });
  return checker ? checker({
    cfg: params.cfg,
    env: params.env
  }) : false;
}
//#endregion /* v9-40bae2877c5eb366 */
