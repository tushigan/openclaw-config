"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = resolveDefaultPluginNpmDir;exports.c = validatePluginId;exports.i = resolveDefaultPluginGitDir;exports.n = matchesExpectedPluginId;exports.o = resolvePluginInstallDir;exports.r = resolveDefaultPluginExtensionsDir;exports.s = safePluginInstallFileName;exports.t = encodePluginInstallDirName;var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
var _installSafePathCFEnKpw = require("./install-safe-path-CFEnKpw5.js");
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/plugins/install-paths.ts
function safePluginInstallFileName(input) {
  return (0, _installSafePathCFEnKpw.i)(input);
}
function encodePluginInstallDirName(pluginId) {
  const trimmed = pluginId.trim();
  if (!trimmed.includes("/")) return (0, _installSafePathCFEnKpw.i)(trimmed);
  return `@${(0, _installSafePathCFEnKpw.a)(trimmed)}`;
}
function validatePluginId(pluginId) {
  const trimmed = pluginId.trim();
  if (!trimmed) return "invalid plugin name: missing";
  if (trimmed.includes("\\")) return "invalid plugin name: path separators not allowed";
  const segments = trimmed.split("/");
  if (segments.some((segment) => !segment)) return "invalid plugin name: malformed scope";
  if (segments.some((segment) => segment === "." || segment === "..")) return "invalid plugin name: reserved path segment";
  if (segments.length === 1) {
    if (trimmed.startsWith("@")) return "invalid plugin name: scoped ids must use @scope/name format";
    return null;
  }
  if (segments.length !== 2) return "invalid plugin name: path separators not allowed";
  if (!segments[0]?.startsWith("@") || segments[0].length < 2) return "invalid plugin name: scoped ids must use @scope/name format";
  return null;
}
function matchesExpectedPluginId(params) {
  if (!params.expectedPluginId) return true;
  if (params.expectedPluginId === params.pluginId) return true;
  return !params.manifestPluginId && params.pluginId === params.npmPluginId && params.expectedPluginId === (0, _installSafePathCFEnKpw.o)(params.npmPluginId);
}
function resolveDefaultPluginExtensionsDir(env = process.env, homedir) {
  return _nodePath.default.join((0, _utilsD5swhEXt.d)(env, homedir), "extensions");
}
function resolveDefaultPluginNpmDir(env = process.env, homedir) {
  return _nodePath.default.join((0, _utilsD5swhEXt.d)(env, homedir), "npm");
}
function resolveDefaultPluginGitDir(env = process.env, homedir) {
  return _nodePath.default.join((0, _utilsD5swhEXt.d)(env, homedir), "git");
}
function resolvePluginInstallDir(pluginId, extensionsDir) {
  const extensionsBase = extensionsDir ? (0, _utilsD5swhEXt.p)(extensionsDir) : resolveDefaultPluginExtensionsDir();
  const pluginIdError = validatePluginId(pluginId);
  if (pluginIdError) throw new Error(pluginIdError);
  const targetDirResult = (0, _installSafePathCFEnKpw.r)({
    baseDir: extensionsBase,
    id: pluginId,
    invalidNameMessage: "invalid plugin name: path traversal detected",
    nameEncoder: encodePluginInstallDirName
  });
  if (!targetDirResult.ok) throw new Error(targetDirResult.error);
  return targetDirResult.path;
}
//#endregion /* v9-b7ea9cc1155d8bf9 */
