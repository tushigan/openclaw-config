"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = sha256HexPrefix;exports.t = redactIdentifier;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _nodeCrypto = _interopRequireDefault(require("node:crypto"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/logging/redact-identifier.ts
function sha256HexPrefix(value, len = 12) {
  const safeLen = Number.isFinite(len) ? Math.max(1, Math.floor(len)) : 12;
  return _nodeCrypto.default.createHash("sha256").update(value).digest("hex").slice(0, safeLen);
}
function redactIdentifier(value, opts) {
  const trimmed = (0, _stringCoerceBje8XVt.c)(value);
  if (!trimmed) return "-";
  return `sha256:${sha256HexPrefix(trimmed, opts?.len ?? 12)}`;
}
//#endregion /* v9-41ab7a54f2a34d7c */
