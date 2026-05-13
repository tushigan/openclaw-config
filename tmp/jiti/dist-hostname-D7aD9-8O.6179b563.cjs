"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = normalizeHostname;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
//#region src/infra/net/hostname.ts
function normalizeHostname(hostname) {
  const normalized = (0, _stringCoerceBje8XVt.a)(hostname).replace(/\.$/, "");
  if (normalized.startsWith("[") && normalized.endsWith("]")) return normalized.slice(1, -1);
  return normalized;
}
//#endregion /* v9-3e862181026d1c15 */
