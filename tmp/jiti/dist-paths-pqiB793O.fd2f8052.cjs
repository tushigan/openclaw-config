"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = resolveTrajectoryPointerFilePath;exports.i = resolveTrajectoryFilePath;exports.n = void 0;exports.o = resolveTrajectoryPointerOpenFlags;exports.r = void 0;exports.s = safeTrajectorySessionFileName;exports.t = void 0;var _homeDirG5LU3LmA = require("./home-dir-g5LU3LmA.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/trajectory/paths.ts
const TRAJECTORY_RUNTIME_CAPTURE_MAX_BYTES = exports.t = 10 * 1024 * 1024;
const TRAJECTORY_RUNTIME_FILE_MAX_BYTES = exports.r = 50 * 1024 * 1024;
const TRAJECTORY_RUNTIME_EVENT_MAX_BYTES = exports.n = 256 * 1024;
function safeTrajectorySessionFileName(sessionId) {
  const safe = sessionId.replaceAll(/[^A-Za-z0-9_-]/g, "_").slice(0, 120);
  return /[A-Za-z0-9]/u.test(safe) ? safe : "session";
}
function resolveTrajectoryPointerOpenFlags(constants = _nodeFs.default.constants) {
  const noFollow = constants.O_NOFOLLOW;
  return constants.O_CREAT | constants.O_TRUNC | constants.O_WRONLY | (typeof noFollow === "number" ? noFollow : 0);
}
function resolveContainedPath(baseDir, fileName) {
  const resolvedBase = _nodePath.default.resolve(baseDir);
  const resolvedFile = _nodePath.default.resolve(resolvedBase, fileName);
  const relative = _nodePath.default.relative(resolvedBase, resolvedFile);
  if (!relative || relative.startsWith("..") || _nodePath.default.isAbsolute(relative)) throw new Error("Trajectory file path escaped its configured directory");
  return resolvedFile;
}
function resolveTrajectoryFilePath(params) {
  const dirOverride = (params.env ?? process.env).OPENCLAW_TRAJECTORY_DIR?.trim();
  if (dirOverride) return resolveContainedPath((0, _homeDirG5LU3LmA.r)(dirOverride), `${safeTrajectorySessionFileName(params.sessionId)}.jsonl`);
  if (!params.sessionFile) return _nodePath.default.join(process.cwd(), `${safeTrajectorySessionFileName(params.sessionId)}.trajectory.jsonl`);
  return params.sessionFile.endsWith(".jsonl") ? `${params.sessionFile.slice(0, -6)}.trajectory.jsonl` : `${params.sessionFile}.trajectory.jsonl`;
}
function resolveTrajectoryPointerFilePath(sessionFile) {
  return sessionFile.endsWith(".jsonl") ? `${sessionFile.slice(0, -6)}.trajectory-path.json` : `${sessionFile}.trajectory-path.json`;
}
//#endregion /* v9-da5ad71e3d37f109 */
