"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = isPathInside;exports.r = isPathInsideWithRealpath;exports.t = extensionUsesSkippedScannerPath;var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/security/scan-paths.ts
function isPathInside(basePath, candidatePath) {
  const base = _nodePath.default.resolve(basePath);
  const candidate = _nodePath.default.resolve(candidatePath);
  const rel = _nodePath.default.relative(base, candidate);
  return rel === "" || !rel.startsWith(`..${_nodePath.default.sep}`) && rel !== ".." && !_nodePath.default.isAbsolute(rel);
}
function safeRealpathSync(filePath) {
  try {
    return _nodeFs.default.realpathSync(filePath);
  } catch {
    return null;
  }
}
function isPathInsideWithRealpath(basePath, candidatePath, opts) {
  if (!isPathInside(basePath, candidatePath)) return false;
  const baseReal = safeRealpathSync(basePath);
  const candidateReal = safeRealpathSync(candidatePath);
  if (!baseReal || !candidateReal) return opts?.requireRealpath === false;
  return isPathInside(baseReal, candidateReal);
}
function extensionUsesSkippedScannerPath(entry) {
  return entry.split(/[\\/]+/).filter(Boolean).some((segment) => segment === "node_modules" || segment.startsWith(".") && segment !== "." && segment !== "..");
}
//#endregion /* v9-f2a5b4e55f463e80 */
