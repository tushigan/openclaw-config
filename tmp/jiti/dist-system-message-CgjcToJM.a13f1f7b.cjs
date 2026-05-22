"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = hasSystemMark;exports.r = prefixSystemMessage;exports.t = void 0; //#region src/infra/system-message.ts
const SYSTEM_MARK = exports.t = "⚙️";
function normalizeSystemText(value) {
  return value.trim();
}
function hasSystemMark(text) {
  return normalizeSystemText(text).startsWith(SYSTEM_MARK);
}
function prefixSystemMessage(text) {
  const normalized = normalizeSystemText(text);
  if (!normalized) return normalized;
  if (hasSystemMark(normalized)) return normalized;
  return `${SYSTEM_MARK} ${normalized}`;
}
//#endregion /* v9-343e8c5740d05cf3 */
