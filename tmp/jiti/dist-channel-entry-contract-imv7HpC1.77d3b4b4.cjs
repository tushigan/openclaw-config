"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = defineBundledChannelSetupEntry;exports.r = loadBundledEntryExportSync;exports.t = defineBundledChannelEntry;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _boundaryFileReadOFRaIDYB = require("./boundary-file-read-oFRaIDYB.js");
var _pluginModuleLoaderCacheB600Kx = require("./plugin-module-loader-cache-B60-0Kx3.js");
var _sdkAliasDiiCKlea = require("./sdk-alias-DiiCKlea.js");
var _configSchemaBV5tVmUb = require("./config-schema-BV5tVmUb.js");
var _pluginLoadProfileCX9TjsiD = require("./plugin-load-profile-CX9TjsiD.js");
var _nodeModule = require("node:module");
var _nodeUrl = require("node:url");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/plugin-sdk/channel-entry-contract.ts
const nodeRequire = (0, _nodeModule.createRequire)("file:///opt/homebrew/lib/node_modules/openclaw/dist/channel-entry-contract-imv7HpC1.js");
const moduleLoaders = /* @__PURE__ */new Map();
const loadedModuleExports = /* @__PURE__ */new Map();
const disableBundledEntrySourceFallbackEnv = "OPENCLAW_DISABLE_BUNDLED_ENTRY_SOURCE_FALLBACK";
function isTruthyEnvFlag(value) {
  return value !== void 0 && !/^(?:0|false)$/iu.test(value.trim());
}
function resolveSpecifierCandidates(modulePath) {
  const ext = (0, _stringCoerceBje8XVt.a)(_nodePath.default.extname(modulePath));
  if (ext === ".js") return [modulePath, modulePath.slice(0, -3) + ".ts"];
  if (ext === ".mjs") return [modulePath, modulePath.slice(0, -4) + ".mts"];
  if (ext === ".cjs") return [modulePath, modulePath.slice(0, -4) + ".cts"];
  return [modulePath];
}
function resolveEntryBoundaryRoot(importMetaUrl) {
  return _nodePath.default.dirname((0, _nodeUrl.fileURLToPath)(importMetaUrl));
}
function addBundledEntryCandidates(candidates, basePath, boundaryRoot) {
  for (const candidate of resolveSpecifierCandidates(basePath)) {
    if (candidates.some((entry) => entry.path === candidate && entry.boundaryRoot === boundaryRoot)) continue;
    candidates.push({
      path: candidate,
      boundaryRoot
    });
  }
}
function resolveBundledEntryModuleCandidates(importMetaUrl, specifier) {
  const importerPath = (0, _nodeUrl.fileURLToPath)(importMetaUrl);
  const importerDir = _nodePath.default.dirname(importerPath);
  const boundaryRoot = resolveEntryBoundaryRoot(importMetaUrl);
  const candidates = [];
  addBundledEntryCandidates(candidates, _nodePath.default.resolve(importerDir, specifier), boundaryRoot);
  const sourceRelativeSpecifier = specifier.replace(/^\.\/src\//u, "./");
  if (sourceRelativeSpecifier !== specifier) addBundledEntryCandidates(candidates, _nodePath.default.resolve(importerDir, sourceRelativeSpecifier), boundaryRoot);
  const packageRoot = (0, _sdkAliasDiiCKlea.l)({
    modulePath: importerPath,
    moduleUrl: importMetaUrl,
    cwd: importerDir,
    argv1: process.argv[1]
  });
  if (!packageRoot) return candidates;
  const distExtensionsRoot = _nodePath.default.join(packageRoot, "dist", "extensions") + _nodePath.default.sep;
  if (!importerPath.startsWith(distExtensionsRoot)) return candidates;
  if (isTruthyEnvFlag(process.env[disableBundledEntrySourceFallbackEnv])) return candidates;
  const pluginDirName = _nodePath.default.basename(importerDir);
  const sourcePluginRoot = _nodePath.default.join(packageRoot, "extensions", pluginDirName);
  if (sourcePluginRoot === boundaryRoot) return candidates;
  addBundledEntryCandidates(candidates, _nodePath.default.resolve(sourcePluginRoot, specifier), sourcePluginRoot);
  if (sourceRelativeSpecifier !== specifier) addBundledEntryCandidates(candidates, _nodePath.default.resolve(sourcePluginRoot, sourceRelativeSpecifier), sourcePluginRoot);
  return candidates;
}
function formatBundledEntryUnknownError(error) {
  if (typeof error === "string") return error;
  if (error === void 0) return "boundary validation failed";
  try {
    return JSON.stringify(error);
  } catch {
    return "non-serializable error";
  }
}
function formatBundledEntryModuleOpenFailure(params) {
  const importerPath = (0, _nodeUrl.fileURLToPath)(params.importMetaUrl);
  const errorDetail = params.failure.error instanceof Error ? params.failure.error.message : formatBundledEntryUnknownError(params.failure.error);
  return [
  `bundled plugin entry "${params.specifier}" failed to open`,
  `from "${importerPath}"`,
  `(resolved "${params.resolvedPath}", plugin root "${params.boundaryRoot}",`,
  `reason "${params.failure.reason}"): ${errorDetail}`].
  join(" ");
}
function resolveBundledEntryModulePath(importMetaUrl, specifier) {
  const candidates = resolveBundledEntryModuleCandidates(importMetaUrl, specifier);
  const fallbackCandidate = candidates[0] ?? {
    path: _nodePath.default.resolve(_nodePath.default.dirname((0, _nodeUrl.fileURLToPath)(importMetaUrl)), specifier),
    boundaryRoot: resolveEntryBoundaryRoot(importMetaUrl)
  };
  let firstFailure = null;
  for (const candidate of candidates) {
    const opened = (0, _boundaryFileReadOFRaIDYB.i)({
      absolutePath: candidate.path,
      rootPath: candidate.boundaryRoot,
      boundaryLabel: "plugin root",
      rejectHardlinks: false,
      skipLexicalRootCheck: true
    });
    if (opened.ok) {
      _nodeFs.default.closeSync(opened.fd);
      return opened.path;
    }
    firstFailure ??= {
      candidate,
      failure: opened
    };
  }
  const failure = firstFailure;
  if (!failure) throw new Error(formatBundledEntryModuleOpenFailure({
    importMetaUrl,
    specifier,
    resolvedPath: fallbackCandidate.path,
    boundaryRoot: fallbackCandidate.boundaryRoot,
    failure: {
      ok: false,
      reason: "path",
      error: /* @__PURE__ */new Error(`ENOENT: no such file or directory, lstat '${fallbackCandidate.path}'`)
    }
  }));
  throw new Error(formatBundledEntryModuleOpenFailure({
    importMetaUrl,
    specifier,
    resolvedPath: failure.candidate.path,
    boundaryRoot: failure.candidate.boundaryRoot,
    failure: failure.failure
  }));
}
function getSourceModuleLoader(modulePath) {
  return (0, _pluginModuleLoaderCacheB600Kx.r)({
    cache: moduleLoaders,
    modulePath,
    importerUrl: "file:///opt/homebrew/lib/node_modules/openclaw/dist/channel-entry-contract-imv7HpC1.js",
    preferBuiltDist: true,
    loaderFilename: "file:///opt/homebrew/lib/node_modules/openclaw/dist/channel-entry-contract-imv7HpC1.js"
  });
}
function canTryNodeRequireBuiltModule(modulePath) {
  return (modulePath.includes(`${_nodePath.default.sep}dist${_nodePath.default.sep}`) || modulePath.includes(`${_nodePath.default.sep}dist-runtime${_nodePath.default.sep}`)) && [
  ".js",
  ".mjs",
  ".cjs"].
  includes((0, _stringCoerceBje8XVt.a)(_nodePath.default.extname(modulePath)));
}
function loadBundledEntryModuleSync(importMetaUrl, specifier, _options = {}) {
  const modulePath = resolveBundledEntryModulePath(importMetaUrl, specifier);
  const cached = loadedModuleExports.get(modulePath);
  if (cached !== void 0) return cached;
  let loaded;
  const profile = (0, _pluginLoadProfileCX9TjsiD.r)();
  const loadStartMs = profile ? performance.now() : 0;
  let sourceLoaderReadyMs = 0;
  if (canTryNodeRequireBuiltModule(modulePath)) try {
    loaded = nodeRequire(modulePath);
  } catch {
    const moduleLoader = getSourceModuleLoader(modulePath);
    sourceLoaderReadyMs = profile ? performance.now() : 0;
    loaded = moduleLoader((0, _pluginModuleLoaderCacheB600Kx.s)(modulePath));
  } else
  {
    const moduleLoader = getSourceModuleLoader(modulePath);
    sourceLoaderReadyMs = profile ? performance.now() : 0;
    loaded = moduleLoader((0, _pluginModuleLoaderCacheB600Kx.s)(modulePath));
  }
  if (profile) {
    const endMs = performance.now();
    console.error((0, _pluginLoadProfileCX9TjsiD.n)({
      phase: "bundled-entry-module-load",
      pluginId: "(bundled-entry)",
      source: modulePath,
      elapsedMs: endMs - loadStartMs,
      extras: [["sourceLoaderCreateMs", sourceLoaderReadyMs ? sourceLoaderReadyMs - loadStartMs : 0], ["sourceLoaderCallMs", sourceLoaderReadyMs ? endMs - sourceLoaderReadyMs : 0]]
    }));
  }
  loadedModuleExports.set(modulePath, loaded);
  return loaded;
}
function loadBundledEntryExportSync(importMetaUrl, reference, options) {
  const loaded = loadBundledEntryModuleSync(importMetaUrl, reference.specifier, options);
  const resolved = loaded && typeof loaded === "object" && "default" in loaded ? loaded.default : loaded;
  if (!reference.exportName) return resolved;
  const record = resolved ?? loaded;
  if (!record || !(reference.exportName in record)) throw new Error(`missing export "${reference.exportName}" from bundled entry module ${reference.specifier}`);
  return record[reference.exportName];
}
function defineBundledChannelEntry({ id, name, description, importMetaUrl, plugin, secrets, configSchema, runtime, accountInspect, features, registerCliMetadata, registerFull }) {
  const resolvedConfigSchema = typeof configSchema === "function" ? configSchema() : configSchema ?? (0, _configSchemaBV5tVmUb.o)();
  const loadChannelPlugin = (options) => loadBundledEntryExportSync(importMetaUrl, plugin, options);
  const loadChannelSecrets = secrets ? (options) => loadBundledEntryExportSync(importMetaUrl, secrets, options) : void 0;
  const loadChannelAccountInspector = accountInspect ? (options) => loadBundledEntryExportSync(importMetaUrl, accountInspect, options) : void 0;
  const setChannelRuntime = runtime ? (pluginRuntime) => {
    loadBundledEntryExportSync(importMetaUrl, runtime)(pluginRuntime);
  } : void 0;
  return {
    kind: "bundled-channel-entry",
    id,
    name,
    description,
    configSchema: resolvedConfigSchema,
    ...(features || accountInspect ? { features: {
        ...features,
        ...(accountInspect ? { accountInspect: true } : {})
      } } : {}),
    register(api) {
      if (api.registrationMode === "cli-metadata") {
        registerCliMetadata?.(api);
        return;
      }
      if (api.registrationMode === "tool-discovery") {
        (0, _pluginLoadProfileCX9TjsiD.t)({
          pluginId: id,
          source: importMetaUrl
        })("bundled-register:registerFull", () => registerFull?.(api));
        return;
      }
      const profile = (0, _pluginLoadProfileCX9TjsiD.t)({
        pluginId: id,
        source: importMetaUrl
      });
      const channelPlugin = profile("bundled-register:loadChannelPlugin", loadChannelPlugin);
      profile("bundled-register:registerChannel", () => api.registerChannel({ plugin: channelPlugin }));
      profile("bundled-register:setChannelRuntime", () => setChannelRuntime?.(api.runtime));
      if (api.registrationMode === "discovery") {
        profile("bundled-register:registerCliMetadata", () => registerCliMetadata?.(api));
        return;
      }
      if (api.registrationMode !== "full") return;
      profile("bundled-register:registerCliMetadata", () => registerCliMetadata?.(api));
      profile("bundled-register:registerFull", () => registerFull?.(api));
    },
    loadChannelPlugin,
    ...(loadChannelSecrets ? { loadChannelSecrets } : {}),
    ...(loadChannelAccountInspector ? { loadChannelAccountInspector } : {}),
    ...(setChannelRuntime ? { setChannelRuntime } : {})
  };
}
function defineBundledChannelSetupEntry({ importMetaUrl, plugin, secrets, runtime, legacyStateMigrations, legacySessionSurface, features }) {
  const setChannelRuntime = runtime ? (pluginRuntime) => {
    loadBundledEntryExportSync(importMetaUrl, runtime)(pluginRuntime);
  } : void 0;
  const loadLegacyStateMigrationDetector = legacyStateMigrations ? (options) => loadBundledEntryExportSync(importMetaUrl, legacyStateMigrations, options) : void 0;
  const loadLegacySessionSurface = legacySessionSurface ? (options) => loadBundledEntryExportSync(importMetaUrl, legacySessionSurface, options) : void 0;
  return {
    kind: "bundled-channel-setup-entry",
    loadSetupPlugin: (options) => loadBundledEntryExportSync(importMetaUrl, plugin, options),
    ...(secrets ? { loadSetupSecrets: (options) => loadBundledEntryExportSync(importMetaUrl, secrets, options) } : {}),
    ...(loadLegacyStateMigrationDetector ? { loadLegacyStateMigrationDetector } : {}),
    ...(loadLegacySessionSurface ? { loadLegacySessionSurface } : {}),
    ...(setChannelRuntime ? { setChannelRuntime } : {}),
    ...(features ? { features } : {})
  };
}
//#endregion /* v9-73031f0fc76c7b47 */
