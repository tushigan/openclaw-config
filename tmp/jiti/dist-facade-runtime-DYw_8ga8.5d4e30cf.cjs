"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = tryLoadActivatedBundledPluginPublicSurfaceModuleSync;exports.i = resetFacadeRuntimeStateForTest;exports.n = loadActivatedBundledPluginPublicSurfaceModuleSync;exports.r = loadBundledPluginPublicSurfaceModuleSync;exports.t = createLazyFacadeValue;var _bundledDirDL2yDGTU = require("./bundled-dir-DL2yDGTU.js");
var _pluginModuleLoaderCacheB600Kx = require("./plugin-module-loader-cache-B60-0Kx3.js");
var _sdkAliasDiiCKlea = require("./sdk-alias-DiiCKlea.js");
var _facadeResolutionSharedC_J6Sr6P = require("./facade-resolution-shared-C_J6Sr6P.js");
var _facadeLoaderCEuC9fQG = require("./facade-loader-CEuC9fQG.js");
var _nodeModule = require("node:module");
var _nodeUrl = require("node:url");
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/plugin-sdk/facade-runtime.ts
function createLazyFacadeValue(loadFacadeModule, key) {
  return (...args) => {
    const value = loadFacadeModule()[key];
    if (typeof value !== "function") return value;
    return value(...args);
  };
}
const OPENCLAW_PACKAGE_ROOT = (0, _sdkAliasDiiCKlea.l)({
  modulePath: (0, _nodeUrl.fileURLToPath)("file:///opt/homebrew/lib/node_modules/openclaw/dist/facade-runtime-DYw_8ga8.js"),
  moduleUrl: "file:///opt/homebrew/lib/node_modules/openclaw/dist/facade-runtime-DYw_8ga8.js"
}) ?? (0, _nodeUrl.fileURLToPath)(new URL("../..", "file:///opt/homebrew/lib/node_modules/openclaw/dist/facade-runtime-DYw_8ga8.js"));
const CURRENT_MODULE_PATH = (0, _nodeUrl.fileURLToPath)("file:///opt/homebrew/lib/node_modules/openclaw/dist/facade-runtime-DYw_8ga8.js");
const OPENCLAW_SOURCE_EXTENSIONS_ROOT = _nodePath.default.resolve(OPENCLAW_PACKAGE_ROOT, "extensions");
function createFacadeResolutionKey(params) {
  const bundledPluginsDir = (0, _bundledDirDL2yDGTU.n)(params.env ?? process.env);
  return (0, _facadeResolutionSharedC_J6Sr6P.t)({
    ...params,
    bundledPluginsDir,
    ...(params.env ? { env: params.env } : {})
  });
}
function resolveRegistryPluginModuleLocation(params) {
  return loadFacadeActivationCheckRuntime().resolveRegistryPluginModuleLocation({
    ...params,
    resolutionKey: createFacadeResolutionKey(params)
  });
}
function resolveFacadeModuleLocationUncached(params) {
  const bundledPluginsDir = (0, _bundledDirDL2yDGTU.n)(params.env ?? process.env);
  const bundledLocation = (0, _facadeResolutionSharedC_J6Sr6P.n)({
    ...params,
    currentModulePath: CURRENT_MODULE_PATH,
    packageRoot: OPENCLAW_PACKAGE_ROOT,
    bundledPluginsDir
  });
  if (bundledLocation) return bundledLocation;
  return resolveRegistryPluginModuleLocation(params);
}
function resolveFacadeModuleLocation(params) {
  return resolveFacadeModuleLocationUncached(params);
}
const nodeRequire = (0, _nodeModule.createRequire)("file:///opt/homebrew/lib/node_modules/openclaw/dist/facade-runtime-DYw_8ga8.js");
const FACADE_ACTIVATION_CHECK_RUNTIME_CANDIDATES = ["./facade-activation-check.runtime.js", "./facade-activation-check.runtime.ts"];
let facadeActivationCheckRuntimeModule;
const facadeActivationCheckRuntimeLoaders = /* @__PURE__ */new Map();
function getFacadeActivationCheckRuntimeSourceLoader(modulePath) {
  return (0, _pluginModuleLoaderCacheB600Kx.r)({
    cache: facadeActivationCheckRuntimeLoaders,
    modulePath,
    importerUrl: "file:///opt/homebrew/lib/node_modules/openclaw/dist/facade-runtime-DYw_8ga8.js",
    loaderFilename: "file:///opt/homebrew/lib/node_modules/openclaw/dist/facade-runtime-DYw_8ga8.js",
    aliasMap: {}
  });
}
function loadFacadeActivationCheckRuntimeFromCandidates(loadCandidate) {
  for (const candidate of FACADE_ACTIVATION_CHECK_RUNTIME_CANDIDATES) try {
    return loadCandidate(candidate);
  } catch {}
}
function loadFacadeActivationCheckRuntime() {
  if (facadeActivationCheckRuntimeModule) return facadeActivationCheckRuntimeModule;
  facadeActivationCheckRuntimeModule = loadFacadeActivationCheckRuntimeFromCandidates((candidate) => nodeRequire(candidate));
  if (facadeActivationCheckRuntimeModule) return facadeActivationCheckRuntimeModule;
  facadeActivationCheckRuntimeModule = loadFacadeActivationCheckRuntimeFromCandidates((candidate) => getFacadeActivationCheckRuntimeSourceLoader(candidate)(candidate));
  if (facadeActivationCheckRuntimeModule) return facadeActivationCheckRuntimeModule;
  throw new Error("Unable to load facade activation check runtime");
}
function loadFacadeModuleAtLocationSync(params) {
  return (0, _facadeLoaderCEuC9fQG.i)(params);
}
function buildFacadeActivationCheckParams(params, location = resolveFacadeModuleLocation(params)) {
  return {
    ...params,
    location,
    sourceExtensionsRoot: OPENCLAW_SOURCE_EXTENSIONS_ROOT,
    resolutionKey: createFacadeResolutionKey(params)
  };
}
function loadBundledPluginPublicSurfaceModuleSync(params) {
  const location = resolveFacadeModuleLocation(params);
  const trackedPluginId = () => loadFacadeActivationCheckRuntime().resolveTrackedFacadePluginId(buildFacadeActivationCheckParams(params, location));
  if (!location) return (0, _facadeLoaderCEuC9fQG.r)({
    ...params,
    trackedPluginId
  });
  return loadFacadeModuleAtLocationSync({
    location,
    trackedPluginId,
    runtimeDeps: {
      pluginId: params.dirName,
      ...(params.env ? { env: params.env } : {})
    }
  });
}
function loadActivatedBundledPluginPublicSurfaceModuleSync(params) {
  loadFacadeActivationCheckRuntime().resolveActivatedBundledPluginPublicSurfaceAccessOrThrow(buildFacadeActivationCheckParams(params));
  return loadBundledPluginPublicSurfaceModuleSync(params);
}
function tryLoadActivatedBundledPluginPublicSurfaceModuleSync(params) {
  if (!loadFacadeActivationCheckRuntime().resolveBundledPluginPublicSurfaceAccess(buildFacadeActivationCheckParams(params)).allowed) return null;
  return loadBundledPluginPublicSurfaceModuleSync(params);
}
function resetFacadeRuntimeStateForTest() {
  (0, _facadeLoaderCEuC9fQG.a)();
  facadeActivationCheckRuntimeModule = void 0;
  facadeActivationCheckRuntimeLoaders.clear();
}
//#endregion /* v9-802279a608fb1762 */
