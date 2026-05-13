"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = loadEnabledBundleConfig;exports.i = inspectBundleServerRuntimeSupport;exports.n = inspectBundleMcpRuntimeSupport;exports.o = readBundleJsonObject;exports.r = loadEnabledBundleMcpConfig;exports.t = extractMcpServerMap;var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
var _boundaryFileReadOFRaIDYB = require("./boundary-file-read-oFRaIDYB.js");
var _discoveryCVL9KJt = require("./discovery-CVL9-KJt.js");
var _configStateWKtsQXM = require("./config-state-wKtsQXM5.js");
var _pluginRegistryCutMFnk = require("./plugin-registry-Cut-MFnk.js");
var _mergePatchC3PIQ2jH = require("./merge-patch-C3PIQ2jH.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/plugins/bundle-config-shared.ts
function readBundleJsonObject(params) {
  const opened = (0, _boundaryFileReadOFRaIDYB.i)({
    absolutePath: _nodePath.default.join(params.rootDir, params.relativePath),
    rootPath: params.rootDir,
    boundaryLabel: "plugin root",
    rejectHardlinks: true
  });
  if (!opened.ok) return params.onOpenFailure?.(opened) ?? {
    ok: true,
    raw: {}
  };
  try {
    const raw = JSON.parse(_nodeFs.default.readFileSync(opened.fd, "utf-8"));
    if (!(0, _utilsD5swhEXt.c)(raw)) return {
      ok: false,
      error: `${params.relativePath} must contain a JSON object`
    };
    return {
      ok: true,
      raw
    };
  } catch (error) {
    return {
      ok: false,
      error: `failed to parse ${params.relativePath}: ${String(error)}`
    };
  } finally {
    _nodeFs.default.closeSync(opened.fd);
  }
}
function resolveBundleJsonOpenFailure(params) {
  return (0, _boundaryFileReadOFRaIDYB.n)(params.failure, {
    path: () => {
      if (params.allowMissing) return {
        ok: true,
        raw: {}
      };
      return {
        ok: false,
        error: `unable to read ${params.relativePath}: path`
      };
    },
    fallback: (failure) => ({
      ok: false,
      error: `unable to read ${params.relativePath}: ${failure.reason}`
    })
  });
}
function inspectBundleServerRuntimeSupport(params) {
  const supportedServerNames = [];
  const unsupportedServerNames = [];
  let hasSupportedServer = false;
  for (const [serverName, server] of Object.entries(params.resolveServers(params.loaded.config))) {
    if (typeof server.command === "string" && server.command.trim().length > 0) {
      hasSupportedServer = true;
      supportedServerNames.push(serverName);
      continue;
    }
    unsupportedServerNames.push(serverName);
  }
  return {
    hasSupportedServer,
    supportedServerNames,
    unsupportedServerNames,
    diagnostics: params.loaded.diagnostics
  };
}
function loadEnabledBundleConfig(params) {
  const normalizedPlugins = (0, _configStateWKtsQXM.s)(params.cfg?.plugins);
  if (!normalizedPlugins.enabled) return {
    config: params.createEmptyConfig(),
    diagnostics: []
  };
  const registry = (0, _pluginRegistryCutMFnk.n)({
    workspaceDir: params.workspaceDir,
    config: params.cfg,
    includeDisabled: true
  });
  const diagnostics = [];
  let merged = params.createEmptyConfig();
  for (const record of registry.plugins) {
    if (record.format !== "bundle" || !record.bundleFormat) continue;
    if (!(0, _configStateWKtsQXM.l)({
      id: record.id,
      origin: record.origin,
      config: normalizedPlugins,
      rootConfig: params.cfg
    }).activated) continue;
    const loaded = params.loadBundleConfig({
      pluginId: record.id,
      rootDir: record.rootDir,
      bundleFormat: record.bundleFormat
    });
    merged = (0, _mergePatchC3PIQ2jH.t)(merged, loaded.config);
    for (const message of loaded.diagnostics) diagnostics.push(params.createDiagnostic(record.id, message));
  }
  return {
    config: merged,
    diagnostics
  };
}
//#endregion
//#region src/plugins/bundle-mcp.ts
const MANIFEST_PATH_BY_FORMAT = {
  claude: _discoveryCVL9KJt.m,
  codex: _discoveryCVL9KJt.h,
  cursor: _discoveryCVL9KJt.g
};
const CLAUDE_PLUGIN_ROOT_PLACEHOLDER = "${CLAUDE_PLUGIN_ROOT}";
function resolveBundleMcpConfigPaths(params) {
  const declared = (0, _discoveryCVL9KJt.b)(params.raw.mcpServers);
  const defaults = _nodeFs.default.existsSync(_nodePath.default.join(params.rootDir, ".mcp.json")) ? [".mcp.json"] : [];
  if (params.bundleFormat === "claude") return (0, _discoveryCVL9KJt.y)(defaults, declared);
  return (0, _discoveryCVL9KJt.y)(defaults, declared);
}
function extractMcpServerMap(raw) {
  if (!(0, _utilsD5swhEXt.c)(raw)) return {};
  const nested = (0, _utilsD5swhEXt.c)(raw.mcpServers) ? raw.mcpServers : (0, _utilsD5swhEXt.c)(raw.servers) ? raw.servers : raw;
  if (!(0, _utilsD5swhEXt.c)(nested)) return {};
  const result = {};
  for (const [serverName, serverRaw] of Object.entries(nested)) {
    if (!(0, _utilsD5swhEXt.c)(serverRaw)) continue;
    result[serverName] = { ...serverRaw };
  }
  return result;
}
function isExplicitRelativePath(value) {
  return value === "." || value === ".." || value.startsWith("./") || value.startsWith("../");
}
function expandBundleRootPlaceholders(value, rootDir) {
  if (!value.includes(CLAUDE_PLUGIN_ROOT_PLACEHOLDER)) return value;
  return value.split(CLAUDE_PLUGIN_ROOT_PLACEHOLDER).join(rootDir);
}
function normalizeBundlePath(targetPath) {
  return _nodePath.default.normalize(_nodePath.default.resolve(targetPath));
}
function normalizeExpandedAbsolutePath(value) {
  return _nodePath.default.isAbsolute(value) ? _nodePath.default.normalize(value) : value;
}
function absolutizeBundleMcpServer(params) {
  const next = { ...params.server };
  if (typeof next.cwd !== "string" && typeof next.workingDirectory !== "string") next.cwd = params.baseDir;
  const command = next.command;
  if (typeof command === "string") {
    const expanded = expandBundleRootPlaceholders(command, params.rootDir);
    next.command = isExplicitRelativePath(expanded) ? _nodePath.default.resolve(params.baseDir, expanded) : normalizeExpandedAbsolutePath(expanded);
  }
  const cwd = next.cwd;
  if (typeof cwd === "string") {
    const expanded = expandBundleRootPlaceholders(cwd, params.rootDir);
    next.cwd = _nodePath.default.isAbsolute(expanded) ? expanded : _nodePath.default.resolve(params.baseDir, expanded);
  }
  const workingDirectory = next.workingDirectory;
  if (typeof workingDirectory === "string") {
    const expanded = expandBundleRootPlaceholders(workingDirectory, params.rootDir);
    next.workingDirectory = _nodePath.default.isAbsolute(expanded) ? _nodePath.default.normalize(expanded) : _nodePath.default.resolve(params.baseDir, expanded);
  }
  if (Array.isArray(next.args)) next.args = next.args.map((entry) => {
    if (typeof entry !== "string") return entry;
    const expanded = expandBundleRootPlaceholders(entry, params.rootDir);
    if (!isExplicitRelativePath(expanded)) return normalizeExpandedAbsolutePath(expanded);
    return _nodePath.default.resolve(params.baseDir, expanded);
  });
  if ((0, _utilsD5swhEXt.c)(next.env)) next.env = Object.fromEntries(Object.entries(next.env).map(([key, value]) => [key, typeof value === "string" ? normalizeExpandedAbsolutePath(expandBundleRootPlaceholders(value, params.rootDir)) : value]));
  return next;
}
function loadBundleFileBackedMcpConfig(params) {
  const rootDir = normalizeBundlePath(params.rootDir);
  const absolutePath = _nodePath.default.resolve(rootDir, params.relativePath);
  const opened = (0, _boundaryFileReadOFRaIDYB.i)({
    absolutePath,
    rootPath: rootDir,
    boundaryLabel: "plugin root",
    rejectHardlinks: true
  });
  if (!opened.ok) return { mcpServers: {} };
  try {
    if (!_nodeFs.default.fstatSync(opened.fd).isFile()) return { mcpServers: {} };
    const servers = extractMcpServerMap(JSON.parse(_nodeFs.default.readFileSync(opened.fd, "utf-8")));
    const baseDir = normalizeBundlePath(_nodePath.default.dirname(absolutePath));
    return { mcpServers: Object.fromEntries(Object.entries(servers).map(([serverName, server]) => [serverName, absolutizeBundleMcpServer({
        rootDir,
        baseDir,
        server
      })])) };
  } finally {
    _nodeFs.default.closeSync(opened.fd);
  }
}
function loadBundleInlineMcpConfig(params) {
  if (!(0, _utilsD5swhEXt.c)(params.raw.mcpServers)) return { mcpServers: {} };
  const baseDir = normalizeBundlePath(params.baseDir);
  const servers = extractMcpServerMap(params.raw.mcpServers);
  return { mcpServers: Object.fromEntries(Object.entries(servers).map(([serverName, server]) => [serverName, absolutizeBundleMcpServer({
      rootDir: baseDir,
      baseDir,
      server
    })])) };
}
function loadBundleMcpConfig(params) {
  const manifestRelativePath = MANIFEST_PATH_BY_FORMAT[params.bundleFormat];
  const manifestLoaded = readBundleJsonObject({
    rootDir: params.rootDir,
    relativePath: manifestRelativePath,
    onOpenFailure: (failure) => resolveBundleJsonOpenFailure({
      failure,
      relativePath: manifestRelativePath,
      allowMissing: params.bundleFormat === "claude"
    })
  });
  if (!manifestLoaded.ok) return {
    config: { mcpServers: {} },
    diagnostics: [manifestLoaded.error]
  };
  let merged = { mcpServers: {} };
  const filePaths = resolveBundleMcpConfigPaths({
    raw: manifestLoaded.raw,
    rootDir: params.rootDir,
    bundleFormat: params.bundleFormat
  });
  for (const relativePath of filePaths) merged = (0, _mergePatchC3PIQ2jH.t)(merged, loadBundleFileBackedMcpConfig({
    rootDir: params.rootDir,
    relativePath
  }));
  merged = (0, _mergePatchC3PIQ2jH.t)(merged, loadBundleInlineMcpConfig({
    raw: manifestLoaded.raw,
    baseDir: params.rootDir
  }));
  return {
    config: merged,
    diagnostics: []
  };
}
function inspectBundleMcpRuntimeSupport(params) {
  const support = inspectBundleServerRuntimeSupport({
    loaded: loadBundleMcpConfig(params),
    resolveServers: (config) => config.mcpServers
  });
  return {
    hasSupportedStdioServer: support.hasSupportedServer,
    supportedServerNames: support.supportedServerNames,
    unsupportedServerNames: support.unsupportedServerNames,
    diagnostics: support.diagnostics
  };
}
function loadEnabledBundleMcpConfig(params) {
  return loadEnabledBundleConfig({
    workspaceDir: params.workspaceDir,
    cfg: params.cfg,
    createEmptyConfig: () => ({ mcpServers: {} }),
    loadBundleConfig: loadBundleMcpConfig,
    createDiagnostic: (pluginId, message) => ({
      pluginId,
      message
    })
  });
}
//#endregion /* v9-119e53742f0e514f */
