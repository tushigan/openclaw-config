"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = onSessionTranscriptUpdate;exports.t = emitSessionTranscriptUpdate;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
//#region src/sessions/transcript-events.ts
const SESSION_TRANSCRIPT_LISTENERS = /* @__PURE__ */new Set();
function onSessionTranscriptUpdate(listener) {
  SESSION_TRANSCRIPT_LISTENERS.add(listener);
  return () => {
    SESSION_TRANSCRIPT_LISTENERS.delete(listener);
  };
}
function emitSessionTranscriptUpdate(update) {
  const normalized = typeof update === "string" ? { sessionFile: update } : {
    sessionFile: update.sessionFile,
    sessionKey: update.sessionKey,
    message: update.message,
    messageId: update.messageId
  };
  const trimmed = (0, _stringCoerceBje8XVt.c)(normalized.sessionFile);
  if (!trimmed) return;
  const nextUpdate = {
    sessionFile: trimmed,
    ...((0, _stringCoerceBje8XVt.c)(normalized.sessionKey) ? { sessionKey: (0, _stringCoerceBje8XVt.c)(normalized.sessionKey) } : {}),
    ...(normalized.message !== void 0 ? { message: normalized.message } : {}),
    ...((0, _stringCoerceBje8XVt.c)(normalized.messageId) ? { messageId: (0, _stringCoerceBje8XVt.c)(normalized.messageId) } : {})
  };
  for (const listener of SESSION_TRANSCRIPT_LISTENERS) try {
    listener(nextUpdate);
  } catch {}
}
//#endregion /* v9-5896bb0a2ce47253 */
