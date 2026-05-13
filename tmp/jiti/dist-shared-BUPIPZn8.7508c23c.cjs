"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = parseEnvValue;exports.c = writeJsonFileSecure;exports.i = parseDotPath;exports.l = writeTextFileAtomic;exports.n = isNonEmptyString;exports.o = readTextFileIfExists;exports.r = normalizePositiveInt;exports.s = toDotPath;exports.t = ensureDirForFile;require("./utils-D5swhEXt.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/secrets/shared.ts
function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}
function parseEnvValue(raw) {
  const trimmed = raw.trim();
  if (trimmed.startsWith("\"") && trimmed.endsWith("\"") || trimmed.startsWith("'") && trimmed.endsWith("'")) return trimmed.slice(1, -1);
  return trimmed;
}
function normalizePositiveInt(value, fallback) {
  if (typeof value === "number" && Number.isFinite(value)) return Math.max(1, Math.floor(value));
  return Math.max(1, Math.floor(fallback));
}
function parseDotPath(pathname) {
  return pathname.split(".").map((segment) => segment.trim()).filter((segment) => segment.length > 0);
}
function toDotPath(segments) {
  return segments.join(".");
}
function ensureDirForFile(filePath) {
  _nodeFs.default.mkdirSync(_nodePath.default.dirname(filePath), {
    recursive: true,
    mode: 448
  });
}
function writeJsonFileSecure(pathname, value) {
  ensureDirForFile(pathname);
  _nodeFs.default.writeFileSync(pathname, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  _nodeFs.default.chmodSync(pathname, 384);
}
function readTextFileIfExists(pathname) {
  if (!_nodeFs.default.existsSync(pathname)) return null;
  return _nodeFs.default.readFileSync(pathname, "utf8");
}
function writeTextFileAtomic(pathname, value, mode = 384) {
  ensureDirForFile(pathname);
  const tempPath = `${pathname}.tmp-${process.pid}-${Date.now()}`;
  _nodeFs.default.writeFileSync(tempPath, value, "utf8");
  _nodeFs.default.chmodSync(tempPath, mode);
  _nodeFs.default.renameSync(tempPath, pathname);
}
//#endregion /* v9-deaf46a3b6e06010 */
