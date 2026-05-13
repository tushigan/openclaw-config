"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = safePathSegmentHashed;exports.i = safeDirName;exports.n = packageNameMatchesId;exports.o = unscopedPackageName;exports.r = resolveSafeInstallDir;exports.t = assertCanonicalPathWithinBase;var _boundaryPathDbcMiy8Y = require("./boundary-path-DbcMiy8Y.js");
var _nodePath = _interopRequireDefault(require("node:path"));
var _promises = _interopRequireDefault(require("node:fs/promises"));
var _nodeCrypto = require("node:crypto");function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/infra/install-safe-path.ts
function unscopedPackageName(name) {
  const trimmed = name.trim();
  if (!trimmed) return trimmed;
  return trimmed.includes("/") ? trimmed.split("/").pop() ?? trimmed : trimmed;
}
function packageNameMatchesId(packageName, id) {
  const trimmedId = id.trim();
  if (!trimmedId) return false;
  const trimmedPackageName = packageName.trim();
  if (!trimmedPackageName) return false;
  return trimmedId === trimmedPackageName || trimmedId === unscopedPackageName(trimmedPackageName);
}
function safeDirName(input) {
  const trimmed = input.trim();
  if (!trimmed) return trimmed;
  return trimmed.replaceAll("/", "__").replaceAll("\\", "__");
}
function safePathSegmentHashed(input) {
  const trimmed = input.trim();
  const base = trimmed.replaceAll(/[\\/]/g, "-").replaceAll(/[^a-zA-Z0-9._-]/g, "-").replaceAll(/-+/g, "-").replaceAll(/^-+/g, "").replaceAll(/-+$/g, "");
  const normalized = base.length > 0 ? base : "skill";
  const safe = normalized === "." || normalized === ".." ? "skill" : normalized;
  const hash = (0, _nodeCrypto.createHash)("sha256").update(trimmed).digest("hex").slice(0, 10);
  if (safe !== trimmed) return `${safe.length > 50 ? safe.slice(0, 50) : safe}-${hash}`;
  if (safe.length > 60) return `${safe.slice(0, 50)}-${hash}`;
  return safe;
}
function resolveSafeInstallDir(params) {
  const encodedName = (params.nameEncoder ?? safeDirName)(params.id);
  const targetDir = _nodePath.default.join(params.baseDir, encodedName);
  const resolvedBase = _nodePath.default.resolve(params.baseDir);
  const resolvedTarget = _nodePath.default.resolve(targetDir);
  const relative = _nodePath.default.relative(resolvedBase, resolvedTarget);
  if (!relative || relative === ".." || relative.startsWith(`..${_nodePath.default.sep}`) || _nodePath.default.isAbsolute(relative)) return {
    ok: false,
    error: params.invalidNameMessage
  };
  return {
    ok: true,
    path: targetDir
  };
}
async function assertCanonicalPathWithinBase(params) {
  const baseDir = _nodePath.default.resolve(params.baseDir);
  const candidatePath = _nodePath.default.resolve(params.candidatePath);
  if (!(0, _boundaryPathDbcMiy8Y.s)(baseDir, candidatePath)) throw new Error(`Invalid path: must stay within ${params.boundaryLabel}`);
  const baseLstat = await _promises.default.lstat(baseDir);
  if (baseLstat.isSymbolicLink()) {
    if (!(await _promises.default.stat(baseDir)).isDirectory()) throw new Error(`Invalid ${params.boundaryLabel}: base directory must resolve to a directory`);
  } else if (!baseLstat.isDirectory()) throw new Error(`Invalid ${params.boundaryLabel}: base directory must be a directory`);
  const baseRealPath = await _promises.default.realpath(baseDir);
  const validateDirectory = async (dirPath) => {
    const resolvedDirPath = _nodePath.default.resolve(dirPath);
    const dirLstat = await _promises.default.lstat(dirPath);
    if (dirLstat.isSymbolicLink()) {
      if (resolvedDirPath !== baseDir) throw new Error(`Invalid path: must stay within ${params.boundaryLabel}`);
      if (!(await _promises.default.stat(dirPath)).isDirectory()) throw new Error(`Invalid path: must stay within ${params.boundaryLabel}`);
    } else if (!dirLstat.isDirectory()) throw new Error(`Invalid path: must stay within ${params.boundaryLabel}`);
    if (!(0, _boundaryPathDbcMiy8Y.s)(baseRealPath, await _promises.default.realpath(dirPath))) throw new Error(`Invalid path: must stay within ${params.boundaryLabel}`);
  };
  try {
    await validateDirectory(candidatePath);
    return;
  } catch (err) {
    if (err.code !== "ENOENT") throw err;
  }
  await validateDirectory(_nodePath.default.dirname(candidatePath));
}
//#endregion /* v9-579d25736a77ef06 */
