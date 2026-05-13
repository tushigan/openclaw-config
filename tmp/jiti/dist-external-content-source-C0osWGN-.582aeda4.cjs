"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = mapHookExternalContentSource;exports.r = resolveHookExternalContentSource;exports.t = isExternalHookSession;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
//#region src/security/external-content-source.ts
function resolveHookExternalContentSource(sessionKey) {
  const normalized = (0, _stringCoerceBje8XVt.a)(sessionKey);
  if (normalized.startsWith("hook:gmail:")) return "gmail";
  if (normalized.startsWith("hook:webhook:") || normalized.startsWith("hook:")) return "webhook";
}
function mapHookExternalContentSource(source) {
  return source === "gmail" ? "email" : "webhook";
}
function isExternalHookSession(sessionKey) {
  return resolveHookExternalContentSource(sessionKey) !== void 0;
}
//#endregion /* v9-a77944ea3c6cdeba */
