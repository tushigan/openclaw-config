"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = listPluginSdkAliasCandidates;exports.c = resolveExtensionApiAlias;exports.d = resolvePluginLoaderTryNative;exports.f = resolvePluginRuntimeModulePath;exports.g = shouldPreferNativeModuleLoad;exports.h = resolvePluginSdkScopedAliasMap;exports.i = isBundledPluginExtensionPath;exports.l = resolveLoaderPackageRoot;exports.m = resolvePluginSdkAliasFile;exports.n = buildPluginLoaderJitiOptions;exports.o = listPluginSdkExportedSubpaths;exports.p = resolvePluginSdkAliasCandidateOrder;exports.r = createPluginLoaderModuleCacheKey;exports.s = normalizeJitiAliasTargetPath;exports.t = buildPluginLoaderAliasMap;exports.u = resolvePluginLoaderModuleConfig;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _openclawRootCRSCIPqz = require("./openclaw-root-CRSCIPqz.js");
var _pluginCachePrimitivesWfwcOrBF = require("./plugin-cache-primitives-WfwcOrBF.js");
var _nodeUrl = require("node:url");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/plugins/sdk-alias.ts
const STARTUP_ARGV1 = process.argv[1];
const pluginSdkPackageJsonByRoot = /* @__PURE__ */new Map();
function normalizeJitiAliasTargetPath(targetPath) {
  return process.platform === "win32" ? targetPath.replace(/\\/g, "/") : targetPath;
}
function resolveLoaderModulePath(params = {}) {
  return params.modulePath ?? (0, _nodeUrl.fileURLToPath)(params.moduleUrl ?? "file:///opt/homebrew/lib/node_modules/openclaw/dist/sdk-alias-DiiCKlea.js");
}
function readPluginSdkPackageJson(packageRoot) {
  const cacheKey = _nodePath.default.resolve(packageRoot);
  if (pluginSdkPackageJsonByRoot.has(cacheKey)) return pluginSdkPackageJsonByRoot.get(cacheKey) ?? null;
  try {
    const pkgRaw = _nodeFs.default.readFileSync(_nodePath.default.join(packageRoot, "package.json"), "utf-8");
    const parsed = JSON.parse(pkgRaw);
    pluginSdkPackageJsonByRoot.set(cacheKey, parsed);
    return parsed;
  } catch {
    pluginSdkPackageJsonByRoot.set(cacheKey, null);
    return null;
  }
}
function isSafePluginSdkSubpathSegment(subpath) {
  return /^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(subpath);
}
function listPluginSdkSubpathsFromPackageJson(pkg) {
  return Object.keys(pkg.exports ?? {}).filter((key) => key.startsWith("./plugin-sdk/")).map((key) => key.slice(13)).filter((subpath) => isSafePluginSdkSubpathSegment(subpath)).toSorted();
}
function hasTrustedOpenClawRootIndicator(params) {
  const packageExports = params.packageJson.exports ?? {};
  if (!Object.prototype.hasOwnProperty.call(packageExports, "./plugin-sdk")) return false;
  const hasCliEntryExport = Object.prototype.hasOwnProperty.call(packageExports, "./cli-entry");
  const hasOpenClawBin = typeof params.packageJson.bin === "string" && (0, _stringCoerceBje8XVt.a)(params.packageJson.bin).includes("openclaw") || typeof params.packageJson.bin === "object" && params.packageJson.bin !== null && typeof params.packageJson.bin.openclaw === "string";
  const hasOpenClawEntrypoint = _nodeFs.default.existsSync(_nodePath.default.join(params.packageRoot, "openclaw.mjs"));
  return hasCliEntryExport || hasOpenClawBin || hasOpenClawEntrypoint;
}
function readPluginSdkSubpathsFromPackageRoot(packageRoot) {
  const pkg = readPluginSdkPackageJson(packageRoot);
  if (!pkg) return null;
  if (!hasTrustedOpenClawRootIndicator({
    packageRoot,
    packageJson: pkg
  })) return null;
  const subpaths = listPluginSdkSubpathsFromPackageJson(pkg);
  return subpaths.length > 0 ? subpaths : null;
}
function resolveTrustedOpenClawRootFromArgvHint(params) {
  if (!params.argv1) return null;
  const packageRoot = (0, _openclawRootCRSCIPqz.n)({
    cwd: params.cwd,
    argv1: params.argv1
  });
  if (!packageRoot) return null;
  const packageJson = readPluginSdkPackageJson(packageRoot);
  if (!packageJson) return null;
  return hasTrustedOpenClawRootIndicator({
    packageRoot,
    packageJson
  }) ? packageRoot : null;
}
function findNearestPluginSdkPackageRoot(startDir, maxDepth = 12) {
  let cursor = _nodePath.default.resolve(startDir);
  for (let i = 0; i < maxDepth; i += 1) {
    if (readPluginSdkSubpathsFromPackageRoot(cursor)) return cursor;
    const parent = _nodePath.default.dirname(cursor);
    if (parent === cursor) break;
    cursor = parent;
  }
  return null;
}
function resolveLoaderPackageRoot(params) {
  const cwd = params.cwd ?? _nodePath.default.dirname(params.modulePath);
  const fromModulePath = (0, _openclawRootCRSCIPqz.n)({ cwd });
  if (fromModulePath) return fromModulePath;
  const argv1 = params.argv1 ?? process.argv[1];
  const moduleUrl = params.moduleUrl ?? (params.modulePath ? void 0 : "file:///opt/homebrew/lib/node_modules/openclaw/dist/sdk-alias-DiiCKlea.js");
  return (0, _openclawRootCRSCIPqz.n)({
    cwd,
    ...(argv1 ? { argv1 } : {}),
    ...(moduleUrl ? { moduleUrl } : {})
  });
}
function resolveLoaderPluginSdkPackageRoot(params) {
  const cwd = params.cwd ?? _nodePath.default.dirname(params.modulePath);
  const fromCwd = (0, _openclawRootCRSCIPqz.n)({ cwd });
  const fromExplicitHints = resolveTrustedOpenClawRootFromArgvHint({
    cwd,
    argv1: params.argv1
  }) ?? (params.moduleUrl ? (0, _openclawRootCRSCIPqz.n)({
    cwd,
    moduleUrl: params.moduleUrl
  }) : null);
  return fromCwd ?? fromExplicitHints ?? findNearestPluginSdkPackageRoot(_nodePath.default.dirname(params.modulePath)) ?? (params.cwd ? findNearestPluginSdkPackageRoot(params.cwd) : null) ?? findNearestPluginSdkPackageRoot(process.cwd());
}
function resolvePluginSdkAliasCandidateOrder(params) {
  if (params.pluginSdkResolution === "dist") return ["dist", "src"];
  if (params.pluginSdkResolution === "src") return ["src", "dist"];
  return params.modulePath.replace(/\\/g, "/").includes("/dist/") || params.isProduction ? ["dist", "src"] : ["src", "dist"];
}
function listPluginSdkAliasCandidates(params) {
  const orderedKinds = resolvePluginSdkAliasCandidateOrder({
    modulePath: params.modulePath,
    isProduction: true,
    pluginSdkResolution: params.pluginSdkResolution
  });
  const packageRoot = resolveLoaderPluginSdkPackageRoot(params);
  if (packageRoot) {
    const candidateMap = {
      src: _nodePath.default.join(packageRoot, "src", "plugin-sdk", params.srcFile),
      dist: _nodePath.default.join(packageRoot, "dist", "plugin-sdk", params.distFile)
    };
    return orderedKinds.map((kind) => candidateMap[kind]);
  }
  let cursor = _nodePath.default.dirname(params.modulePath);
  const candidates = [];
  for (let i = 0; i < 6; i += 1) {
    const candidateMap = {
      src: _nodePath.default.join(cursor, "src", "plugin-sdk", params.srcFile),
      dist: _nodePath.default.join(cursor, "dist", "plugin-sdk", params.distFile)
    };
    for (const kind of orderedKinds) candidates.push(candidateMap[kind]);
    const parent = _nodePath.default.dirname(cursor);
    if (parent === cursor) break;
    cursor = parent;
  }
  return candidates;
}
function resolvePluginSdkAliasFile(params) {
  try {
    const modulePath = resolveLoaderModulePath(params);
    for (const candidate of listPluginSdkAliasCandidates({
      srcFile: params.srcFile,
      distFile: params.distFile,
      modulePath,
      argv1: params.argv1,
      cwd: params.cwd,
      moduleUrl: params.moduleUrl,
      pluginSdkResolution: params.pluginSdkResolution
    })) if (_nodeFs.default.existsSync(candidate)) return candidate;
  } catch {}
  return null;
}
const MAX_PLUGIN_LOADER_ALIAS_CACHE_ENTRIES = 512;
const cachedPluginSdkExportedSubpaths = new _pluginCachePrimitivesWfwcOrBF.t(MAX_PLUGIN_LOADER_ALIAS_CACHE_ENTRIES);
const cachedPluginSdkScopedAliasMaps = new _pluginCachePrimitivesWfwcOrBF.t(MAX_PLUGIN_LOADER_ALIAS_CACHE_ENTRIES);
const PLUGIN_SDK_PACKAGE_NAMES = ["openclaw/plugin-sdk", "@openclaw/plugin-sdk"];
const PLUGIN_SDK_SOURCE_CANDIDATE_EXTENSIONS = [
".ts",
".mts",
".js",
".mjs",
".cts",
".cjs"];

const BUNDLED_PLUGIN_PUBLIC_SURFACE_SOURCE_PATTERN = /^(?:api|runtime-api|test-api|.+-api)$/u;
const JS_STATIC_RELATIVE_DEPENDENCY_PATTERN = /(?:\bfrom\s*["']|\bimport\s*\(\s*["']|\brequire\s*\(\s*["'])(\.{1,2}\/[^"']+)["']/g;
function isUsableDistPluginSdkArtifact(candidate) {
  if (!_nodeFs.default.existsSync(candidate)) return false;
  switch ((0, _stringCoerceBje8XVt.a)(_nodePath.default.extname(candidate))) {
    case ".js":
    case ".mjs":
    case ".cjs":break;
    default:return true;
  }
  try {
    const source = _nodeFs.default.readFileSync(candidate, "utf-8");
    for (const match of source.matchAll(JS_STATIC_RELATIVE_DEPENDENCY_PATTERN)) {
      const specifier = match[1];
      if (!specifier || _nodeFs.default.existsSync(_nodePath.default.resolve(_nodePath.default.dirname(candidate), specifier))) continue;
      return false;
    }
  } catch {
    return false;
  }
  return true;
}
function readPrivateLocalOnlyPluginSdkSubpaths(packageRoot) {
  try {
    const raw = _nodeFs.default.readFileSync(_nodePath.default.join(packageRoot, "scripts", "lib", "plugin-sdk-private-local-only-subpaths.json"), "utf-8");
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((subpath) => isSafePluginSdkSubpathSegment(subpath));
  } catch {
    return [];
  }
}
function readBundledPluginPackageName(packageJsonPath) {
  try {
    const parsed = JSON.parse(_nodeFs.default.readFileSync(packageJsonPath, "utf-8"));
    const name = typeof parsed.name === "string" ? parsed.name.trim() : "";
    return name.startsWith("@openclaw/") ? name : null;
  } catch {
    return null;
  }
}
function isBundledPluginPublicSurfaceSourceBasename(params) {
  if (params.basename === "test-api") return params.includePrivateQa;
  return BUNDLED_PLUGIN_PUBLIC_SURFACE_SOURCE_PATTERN.test(params.basename);
}
function listBundledPluginPublicSurfaceSourceBasenames(params) {
  try {
    return _nodeFs.default.readdirSync(params.extensionSourceRoot, { withFileTypes: true }).filter((entry) => entry.isFile()).map((entry) => entry.name).flatMap((fileName) => {
      const ext = PLUGIN_SDK_SOURCE_CANDIDATE_EXTENSIONS.find((candidateExt) => fileName.endsWith(candidateExt));
      if (!ext) return [];
      const basename = fileName.slice(0, -ext.length);
      return isBundledPluginPublicSurfaceSourceBasename({
        basename,
        includePrivateQa: params.includePrivateQa
      }) ? [basename] : [];
    }).toSorted();
  } catch {
    return [];
  }
}
function resolveBundledPluginPublicSurfaceAliasTarget(params) {
  for (const kind of params.orderedKinds) {
    if (kind === "dist") {
      const candidate = _nodePath.default.join(params.packageRoot, "dist", "extensions", params.dirName, `${params.basename}.js`);
      if (_nodeFs.default.existsSync(candidate)) return candidate;
      continue;
    }
    for (const ext of PLUGIN_SDK_SOURCE_CANDIDATE_EXTENSIONS) {
      const candidate = _nodePath.default.join(params.packageRoot, "extensions", params.dirName, `${params.basename}${ext}`);
      if (_nodeFs.default.existsSync(candidate)) return candidate;
    }
  }
  return null;
}
function resolveBundledPluginPackagePublicSurfaceAliasMap(params) {
  const packageRoot = resolveLoaderPluginSdkPackageRoot(params);
  if (!packageRoot) return {};
  const extensionsRoot = _nodePath.default.join(packageRoot, "extensions");
  let extensionDirs;
  try {
    extensionDirs = _nodeFs.default.readdirSync(extensionsRoot, { withFileTypes: true });
  } catch {
    return {};
  }
  const orderedKinds = resolvePluginSdkAliasCandidateOrder({
    modulePath: params.modulePath,
    isProduction: true,
    pluginSdkResolution: params.pluginSdkResolution
  });
  const includePrivateQa = shouldIncludePrivateLocalOnlyPluginSdkSubpaths();
  const aliasMap = {};
  for (const entry of extensionDirs) {
    if (!entry.isDirectory()) continue;
    const dirName = entry.name;
    const packageName = readBundledPluginPackageName(_nodePath.default.join(extensionsRoot, dirName, "package.json"));
    if (!packageName) continue;
    for (const basename of listBundledPluginPublicSurfaceSourceBasenames({
      extensionSourceRoot: _nodePath.default.join(extensionsRoot, dirName),
      includePrivateQa
    })) {
      const target = resolveBundledPluginPublicSurfaceAliasTarget({
        packageRoot,
        dirName,
        basename,
        orderedKinds
      });
      if (!target) continue;
      aliasMap[`${packageName}/${basename}.js`] = normalizeJitiAliasTargetPath(target);
    }
  }
  return aliasMap;
}
function shouldIncludePrivateLocalOnlyPluginSdkSubpaths() {
  return process.env.OPENCLAW_ENABLE_PRIVATE_QA_CLI === "1";
}
function hasPluginSdkSubpathArtifact(packageRoot, subpath) {
  if (isUsableDistPluginSdkArtifact(_nodePath.default.join(packageRoot, "dist", "plugin-sdk", `${subpath}.js`))) return true;
  return PLUGIN_SDK_SOURCE_CANDIDATE_EXTENSIONS.some((ext) => _nodeFs.default.existsSync(_nodePath.default.join(packageRoot, "src", "plugin-sdk", `${subpath}${ext}`)));
}
function listDistPluginSdkArtifactSubpaths(packageRoot) {
  try {
    const distPluginSdkDir = _nodePath.default.join(packageRoot, "dist", "plugin-sdk");
    return new Set(_nodeFs.default.readdirSync(distPluginSdkDir, { withFileTypes: true }).filter((entry) => entry.isFile() && entry.name.endsWith(".js")).map((entry) => entry.name.slice(0, -3)).filter((subpath) => isSafePluginSdkSubpathSegment(subpath)));
  } catch {
    return /* @__PURE__ */new Set();
  }
}
function listPrivateLocalOnlyPluginSdkSubpaths(packageRoot) {
  if (!shouldIncludePrivateLocalOnlyPluginSdkSubpaths()) return [];
  return readPrivateLocalOnlyPluginSdkSubpaths(packageRoot).filter((subpath) => hasPluginSdkSubpathArtifact(packageRoot, subpath));
}
function listPluginSdkExportedSubpaths(params = {}) {
  const packageRoot = resolveLoaderPluginSdkPackageRoot({
    modulePath: params.modulePath ?? (0, _nodeUrl.fileURLToPath)("file:///opt/homebrew/lib/node_modules/openclaw/dist/sdk-alias-DiiCKlea.js"),
    argv1: params.argv1,
    moduleUrl: params.moduleUrl
  });
  if (!packageRoot) return [];
  const cacheKey = `${packageRoot}::privateQa=${shouldIncludePrivateLocalOnlyPluginSdkSubpaths() ? "1" : "0"}`;
  const cached = cachedPluginSdkExportedSubpaths.get(cacheKey);
  if (cached) return cached;
  const subpaths = [...new Set([...(readPluginSdkSubpathsFromPackageRoot(packageRoot) ?? []), ...listPrivateLocalOnlyPluginSdkSubpaths(packageRoot)])].toSorted();
  cachedPluginSdkExportedSubpaths.set(cacheKey, subpaths);
  return subpaths;
}
function resolvePluginSdkScopedAliasMap(params = {}) {
  const modulePath = params.modulePath ?? (0, _nodeUrl.fileURLToPath)("file:///opt/homebrew/lib/node_modules/openclaw/dist/sdk-alias-DiiCKlea.js");
  const packageRoot = resolveLoaderPluginSdkPackageRoot({
    modulePath,
    argv1: params.argv1,
    moduleUrl: params.moduleUrl
  });
  if (!packageRoot) return {};
  const orderedKinds = resolvePluginSdkAliasCandidateOrder({
    modulePath,
    isProduction: true,
    pluginSdkResolution: params.pluginSdkResolution
  });
  const cacheKey = `${packageRoot}::${orderedKinds.join(",")}::privateQa=${shouldIncludePrivateLocalOnlyPluginSdkSubpaths() ? "1" : "0"}`;
  const cached = cachedPluginSdkScopedAliasMaps.get(cacheKey);
  if (cached) return cached;
  const aliasMap = {};
  const distPluginSdkArtifacts = orderedKinds.includes("dist") ? listDistPluginSdkArtifactSubpaths(packageRoot) : /* @__PURE__ */new Set();
  for (const subpath of listPluginSdkExportedSubpaths({
    modulePath,
    argv1: params.argv1,
    moduleUrl: params.moduleUrl,
    pluginSdkResolution: params.pluginSdkResolution
  })) for (const kind of orderedKinds) {
    if (kind === "dist") {
      if (!distPluginSdkArtifacts.has(subpath)) continue;
      const candidate = _nodePath.default.join(packageRoot, "dist", "plugin-sdk", `${subpath}.js`);
      if (isUsableDistPluginSdkArtifact(candidate)) {
        for (const packageName of PLUGIN_SDK_PACKAGE_NAMES) aliasMap[`${packageName}/${subpath}`] = candidate;
        break;
      }
      continue;
    }
    for (const ext of PLUGIN_SDK_SOURCE_CANDIDATE_EXTENSIONS) {
      const candidate = _nodePath.default.join(packageRoot, "src", "plugin-sdk", `${subpath}${ext}`);
      if (!_nodeFs.default.existsSync(candidate)) continue;
      for (const packageName of PLUGIN_SDK_PACKAGE_NAMES) aliasMap[`${packageName}/${subpath}`] = candidate;
      break;
    }
    if (Object.prototype.hasOwnProperty.call(aliasMap, `openclaw/plugin-sdk/${subpath}`)) break;
  }
  cachedPluginSdkScopedAliasMaps.set(cacheKey, aliasMap);
  return aliasMap;
}
function resolveExtensionApiAlias(params = {}) {
  try {
    const modulePath = resolveLoaderModulePath(params);
    const packageRoot = resolveLoaderPackageRoot({
      ...params,
      modulePath
    });
    if (!packageRoot) return null;
    const orderedKinds = resolvePluginSdkAliasCandidateOrder({
      modulePath,
      isProduction: true,
      pluginSdkResolution: params.pluginSdkResolution
    });
    for (const kind of orderedKinds) {
      if (kind === "dist") {
        const candidate = _nodePath.default.join(packageRoot, "dist", "extensionAPI.js");
        if (_nodeFs.default.existsSync(candidate)) return candidate;
        continue;
      }
      for (const ext of PLUGIN_SDK_SOURCE_CANDIDATE_EXTENSIONS) {
        const candidate = _nodePath.default.join(packageRoot, "src", `extensionAPI${ext}`);
        if (_nodeFs.default.existsSync(candidate)) return candidate;
      }
    }
  } catch {}
  return null;
}
const JITI_NORMALIZED_ALIAS_SYMBOL = Symbol.for("pathe:normalizedAlias");
const JITI_ALIAS_ROOT_SENTINELS = new Set([
"/",
"\\",
void 0]
);
const aliasMapCache = new _pluginCachePrimitivesWfwcOrBF.t(MAX_PLUGIN_LOADER_ALIAS_CACHE_ENTRIES);
const normalizedJitiAliasMapCache = new _pluginCachePrimitivesWfwcOrBF.t(MAX_PLUGIN_LOADER_ALIAS_CACHE_ENTRIES);
const pluginLoaderModuleConfigCache = new _pluginCachePrimitivesWfwcOrBF.t(MAX_PLUGIN_LOADER_ALIAS_CACHE_ENTRIES);
function hasJitiNormalizedAliasMarker(aliasMap) {
  return Boolean(aliasMap[JITI_NORMALIZED_ALIAS_SYMBOL]);
}
function createJitiAliasContentCacheKey(aliasMap) {
  return JSON.stringify(Object.entries(aliasMap).toSorted(([left], [right]) => left.localeCompare(right)));
}
function normalizePluginLoaderAliasMapForJiti(aliasMap) {
  if (hasJitiNormalizedAliasMarker(aliasMap)) return aliasMap;
  const cacheKey = createJitiAliasContentCacheKey(aliasMap);
  const cached = normalizedJitiAliasMapCache.get(cacheKey);
  if (cached) return cached;
  const normalizedAliasMap = Object.fromEntries(Object.entries(aliasMap).toSorted(([left], [right]) => right.split("/").length - left.split("/").length));
  for (const aliasKey in normalizedAliasMap) for (const candidateKey in normalizedAliasMap) {
    if (candidateKey === aliasKey || aliasKey.startsWith(candidateKey) || !normalizedAliasMap[aliasKey]?.startsWith(candidateKey) || !JITI_ALIAS_ROOT_SENTINELS.has(normalizedAliasMap[aliasKey]?.[candidateKey.length])) continue;
    normalizedAliasMap[aliasKey] = normalizedAliasMap[candidateKey] + normalizedAliasMap[aliasKey].slice(candidateKey.length);
  }
  Object.defineProperty(normalizedAliasMap, JITI_NORMALIZED_ALIAS_SYMBOL, {
    value: true,
    enumerable: false
  });
  normalizedJitiAliasMapCache.set(cacheKey, normalizedAliasMap);
  return normalizedAliasMap;
}
function buildPluginLoaderAliasMapCacheKey(params) {
  return [
  params.modulePath,
  params.argv1 ?? "",
  params.moduleUrl ?? "",
  params.pluginSdkResolution,
  process.cwd(),
  "production",
  shouldIncludePrivateLocalOnlyPluginSdkSubpaths() ? "private-qa" : "public"].
  join("\0");
}
function buildPluginLoaderModuleConfigCacheKey(params) {
  return [buildPluginLoaderAliasMapCacheKey({
    modulePath: params.modulePath,
    argv1: params.argv1,
    moduleUrl: params.moduleUrl,
    pluginSdkResolution: params.pluginSdkResolution ?? "auto"
  }), params.preferBuiltDist === true ? "prefer-built-dist" : "default-dist"].join("\0");
}
function buildPluginLoaderAliasMap(modulePath, argv1 = STARTUP_ARGV1, moduleUrl, pluginSdkResolution = "auto") {
  const cacheKey = buildPluginLoaderAliasMapCacheKey({
    modulePath,
    argv1,
    moduleUrl,
    pluginSdkResolution
  });
  const cached = aliasMapCache.get(cacheKey);
  if (cached) return cached;
  const pluginSdkAlias = resolvePluginSdkAliasFile({
    srcFile: "root-alias.cjs",
    distFile: "root-alias.cjs",
    modulePath,
    argv1,
    moduleUrl,
    pluginSdkResolution
  });
  const extensionApiAlias = resolveExtensionApiAlias({
    modulePath,
    pluginSdkResolution
  });
  const result = {
    ...(extensionApiAlias ? { "openclaw/extension-api": normalizeJitiAliasTargetPath(extensionApiAlias) } : {}),
    ...resolveBundledPluginPackagePublicSurfaceAliasMap({
      modulePath,
      argv1,
      moduleUrl,
      pluginSdkResolution
    }),
    ...(pluginSdkAlias ? Object.fromEntries(PLUGIN_SDK_PACKAGE_NAMES.map((packageName) => [packageName, normalizeJitiAliasTargetPath(pluginSdkAlias)])) : {}),
    ...Object.fromEntries(Object.entries(resolvePluginSdkScopedAliasMap({
      modulePath,
      argv1,
      moduleUrl,
      pluginSdkResolution
    })).map(([key, value]) => [key, normalizeJitiAliasTargetPath(value)]))
  };
  aliasMapCache.set(cacheKey, result);
  return result;
}
function resolvePluginRuntimeModulePath(params = {}) {
  try {
    const modulePath = resolveLoaderModulePath(params);
    const orderedKinds = resolvePluginSdkAliasCandidateOrder({
      modulePath,
      isProduction: true,
      pluginSdkResolution: params.pluginSdkResolution
    });
    const packageRoot = resolveLoaderPackageRoot({
      ...params,
      modulePath
    });
    const candidates = packageRoot ? orderedKinds.map((kind) => kind === "src" ? _nodePath.default.join(packageRoot, "src", "plugins", "runtime", "index.ts") : _nodePath.default.join(packageRoot, "dist", "plugins", "runtime", "index.js")) : [_nodePath.default.join(_nodePath.default.dirname(modulePath), "runtime", "index.ts"), _nodePath.default.join(_nodePath.default.dirname(modulePath), "runtime", "index.js")];
    for (const candidate of candidates) if (_nodeFs.default.existsSync(candidate)) return candidate;
  } catch {}
  return null;
}
function buildPluginLoaderJitiOptions(aliasMap) {
  const hasAliases = Object.keys(aliasMap).length > 0;
  const jitiAliasMap = hasAliases ? normalizePluginLoaderAliasMapForJiti(aliasMap) : aliasMap;
  return {
    interopDefault: true,
    tryNative: true,
    extensions: [
    ".ts",
    ".tsx",
    ".mts",
    ".cts",
    ".mtsx",
    ".ctsx",
    ".js",
    ".mjs",
    ".cjs",
    ".json"],

    ...(hasAliases ? { alias: jitiAliasMap } : {})
  };
}
function supportsNativeModuleRuntime() {
  return typeof process.versions.bun !== "string";
}
function isBundledPluginDistModulePath(modulePath) {
  return modulePath.replace(/\\/g, "/").includes("/dist/extensions/");
}
function shouldPreferNativeModuleLoad(modulePath) {
  if (!supportsNativeModuleRuntime()) return false;
  switch ((0, _stringCoerceBje8XVt.a)(_nodePath.default.extname(modulePath))) {
    case ".js":
    case ".mjs":
    case ".cjs":
    case ".json":return true;
    default:return false;
  }
}
function resolvePluginLoaderTryNative(modulePath, options) {
  if (isBundledPluginDistModulePath(modulePath)) return shouldPreferNativeModuleLoad(modulePath);
  return shouldPreferNativeModuleLoad(modulePath) || supportsNativeModuleRuntime() && options?.preferBuiltDist === true && modulePath.includes(`${_nodePath.default.sep}dist${_nodePath.default.sep}`);
}
function createPluginLoaderModuleCacheKey(params) {
  return JSON.stringify({
    tryNative: params.tryNative,
    aliasMap: Object.entries(params.aliasMap).toSorted(([left], [right]) => left.localeCompare(right))
  });
}
function resolvePluginLoaderModuleConfig(params) {
  const configCacheKey = buildPluginLoaderModuleConfigCacheKey(params);
  const cached = pluginLoaderModuleConfigCache.get(configCacheKey);
  if (cached) return cached;
  const tryNative = resolvePluginLoaderTryNative(params.modulePath, params.preferBuiltDist ? { preferBuiltDist: true } : {});
  const aliasMap = buildPluginLoaderAliasMap(params.modulePath, params.argv1, params.moduleUrl, params.pluginSdkResolution);
  const result = {
    tryNative,
    aliasMap,
    cacheKey: createPluginLoaderModuleCacheKey({
      tryNative,
      aliasMap
    })
  };
  pluginLoaderModuleConfigCache.set(configCacheKey, result);
  return result;
}
function isBundledPluginExtensionPath(params) {
  const normalizedModulePath = _nodePath.default.resolve(params.modulePath);
  return [
  params.bundledPluginsDir ? _nodePath.default.resolve(params.bundledPluginsDir) : null,
  _nodePath.default.join(params.openClawPackageRoot, "extensions"),
  _nodePath.default.join(params.openClawPackageRoot, "dist", "extensions"),
  _nodePath.default.join(params.openClawPackageRoot, "dist-runtime", "extensions")].
  filter((root) => typeof root === "string").some((root) => normalizedModulePath === root || normalizedModulePath.startsWith(`${root}${_nodePath.default.sep}`));
}
//#endregion /* v9-d7f8e22ad1203cb6 */
