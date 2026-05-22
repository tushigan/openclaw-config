"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = resolveGroupAllowFromSources;exports.n = isSenderIdAllowed;exports.r = mergeDmAllowFromSources;exports.t = firstDefined;var _stringNormalizationC5SGsaST = require("./string-normalization-C5SGsaST.js");
//#region src/channels/allow-from.ts
function mergeDmAllowFromSources(params) {
  const storeEntries = params.dmPolicy === "allowlist" || params.dmPolicy === "open" ? [] : params.storeAllowFrom ?? [];
  return (0, _stringNormalizationC5SGsaST.s)([...(params.allowFrom ?? []), ...storeEntries]);
}
function resolveGroupAllowFromSources(params) {
  const explicitGroupAllowFrom = Array.isArray(params.groupAllowFrom) && params.groupAllowFrom.length > 0 ? params.groupAllowFrom : void 0;
  return (0, _stringNormalizationC5SGsaST.s)(explicitGroupAllowFrom ? explicitGroupAllowFrom : params.fallbackToAllowFrom === false ? [] : params.allowFrom ?? []);
}
function firstDefined(...values) {
  for (const value of values) if (value !== void 0) return value;
}
function isSenderIdAllowed(allow, senderId, allowWhenEmpty) {
  if (!allow.hasEntries) return allowWhenEmpty;
  if (allow.hasWildcard) return true;
  if (!senderId) return false;
  return allow.entries.includes(senderId);
}
//#endregion /* v9-64ddd51cd400304e */
