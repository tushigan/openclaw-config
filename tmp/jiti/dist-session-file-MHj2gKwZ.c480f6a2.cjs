"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = resolveAndPersistSessionFile;var _pathsDG09LEN = require("./paths-DG09LE-n.js");
var _storeDvxAjGkI = require("./store-DvxAjGkI.js");
//#region src/config/sessions/session-file.ts
async function resolveAndPersistSessionFile(params) {
  const { sessionId, sessionKey, sessionStore, storePath } = params;
  const now = Date.now();
  const baseEntry = params.sessionEntry ?? sessionStore[sessionKey] ?? {
    sessionId,
    updatedAt: now,
    sessionStartedAt: now
  };
  const shouldReusePersistedSessionFile = baseEntry.sessionId === sessionId;
  const fallbackSessionFile = params.fallbackSessionFile?.trim();
  const sessionFile = (0, _pathsDG09LEN.a)(sessionId, !shouldReusePersistedSessionFile ? fallbackSessionFile ? {
    ...baseEntry,
    sessionFile: fallbackSessionFile
  } : {
    ...baseEntry,
    sessionFile: void 0
  } : !baseEntry.sessionFile && fallbackSessionFile ? {
    ...baseEntry,
    sessionFile: fallbackSessionFile
  } : baseEntry, {
    agentId: params.agentId,
    sessionsDir: params.sessionsDir
  });
  const persistedEntry = {
    ...baseEntry,
    sessionId,
    updatedAt: now,
    sessionStartedAt: baseEntry.sessionId === sessionId ? baseEntry.sessionStartedAt ?? now : now,
    sessionFile
  };
  if (baseEntry.sessionId !== sessionId || baseEntry.sessionFile !== sessionFile) {
    sessionStore[sessionKey] = persistedEntry;
    await (0, _storeDvxAjGkI.o)(storePath, (store) => {
      store[sessionKey] = {
        ...store[sessionKey],
        ...persistedEntry
      };
    }, params.activeSessionKey || params.maintenanceConfig ? {
      ...(params.activeSessionKey ? { activeSessionKey: params.activeSessionKey } : {}),
      ...(params.maintenanceConfig ? { maintenanceConfig: params.maintenanceConfig } : {})
    } : void 0);
    return {
      sessionFile,
      sessionEntry: persistedEntry
    };
  }
  sessionStore[sessionKey] = persistedEntry;
  return {
    sessionFile,
    sessionEntry: persistedEntry
  };
}
//#endregion /* v9-987aba28355d1dfb */
