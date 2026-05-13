"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = resolveSessionStoreKey;exports.i = resolveSessionStoreAgentId;exports.n = canonicalizeSessionKeyForAgent;exports.o = resolveStoredSessionKeyForAgentStore;exports.r = canonicalizeSpawnedByForAgent;exports.s = resolveStoredSessionOwnerAgentId;exports.t = loadCombinedSessionStoreForGateway;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _sessionKeyUtils8PXPWO4Z = require("./session-key-utils-8PXPWO4Z.js");
var _sessionKeyC0K0uhmG = require("./session-key-C0K0uhmG.js");
var _agentScopeB6RIBoEj = require("./agent-scope-B6RIBoEj.js");
var _mainSessionC7L7pyed = require("./main-session-C7L7pyed.js");
var _pathsDG09LEN = require("./paths-DG09LE-n.js");
var _storeLoadDjtlQRVG = require("./store-load-DjtlQRVG.js");
var _targetsDjI6H8v = require("./targets-DjI6H-8v.js");
//#region src/gateway/session-store-key.ts
function canonicalizeSessionKeyForAgent(agentId, key) {
  const lowered = (0, _stringCoerceBje8XVt.a)(key);
  if (lowered === "global" || lowered === "unknown") return lowered;
  if (lowered.startsWith("agent:")) return lowered;
  return `agent:${(0, _sessionKeyC0K0uhmG.c)(agentId)}:${lowered}`;
}
function resolveDefaultStoreAgentId(cfg) {
  return (0, _sessionKeyC0K0uhmG.c)((0, _agentScopeB6RIBoEj.S)(cfg));
}
function shouldRemapLegacyDefaultMainAlias(cfg, parsed, options) {
  if ((0, _sessionKeyC0K0uhmG.c)(parsed.agentId) !== "main" || (0, _agentScopeB6RIBoEj._)(cfg).includes("main")) return false;
  const defaultAgentId = resolveDefaultStoreAgentId(cfg);
  if (options?.storeAgentId && (0, _sessionKeyC0K0uhmG.c)(options.storeAgentId) !== defaultAgentId) return false;
  const rest = (0, _stringCoerceBje8XVt.a)(parsed.rest);
  const mainKey = (0, _sessionKeyC0K0uhmG.l)(cfg.session?.mainKey);
  return rest === "main" || rest === mainKey;
}
function resolveParsedSessionStoreKey(cfg, raw, parsed, options) {
  if (!shouldRemapLegacyDefaultMainAlias(cfg, parsed, options)) return {
    agentId: (0, _sessionKeyC0K0uhmG.c)(parsed.agentId),
    sessionKey: (0, _stringCoerceBje8XVt.a)(raw)
  };
  const agentId = resolveDefaultStoreAgentId(cfg);
  return {
    agentId,
    sessionKey: `agent:${agentId}:${(0, _stringCoerceBje8XVt.a)(parsed.rest)}`
  };
}
function resolveSessionStoreKey(params) {
  const raw = (0, _stringCoerceBje8XVt.c)(params.sessionKey) ?? "";
  if (!raw) return raw;
  const rawLower = (0, _stringCoerceBje8XVt.a)(raw);
  if (rawLower === "global" || rawLower === "unknown") return rawLower;
  const parsed = (0, _sessionKeyUtils8PXPWO4Z.o)(raw);
  if (parsed) {
    const resolved = resolveParsedSessionStoreKey(params.cfg, raw, parsed, { storeAgentId: params.storeAgentId });
    const canonical = (0, _mainSessionC7L7pyed.t)({
      cfg: params.cfg,
      agentId: resolved.agentId,
      sessionKey: resolved.sessionKey
    });
    if (canonical !== resolved.sessionKey) return canonical;
    return resolved.sessionKey;
  }
  const lowered = (0, _stringCoerceBje8XVt.a)(raw);
  const rawMainKey = (0, _sessionKeyC0K0uhmG.l)(params.cfg.session?.mainKey);
  if (lowered === "main" || lowered === rawMainKey) return (0, _mainSessionC7L7pyed.i)(params.cfg);
  return canonicalizeSessionKeyForAgent(resolveDefaultStoreAgentId(params.cfg), lowered);
}
function resolveSessionStoreAgentId(cfg, canonicalKey) {
  if (canonicalKey === "global" || canonicalKey === "unknown") return resolveDefaultStoreAgentId(cfg);
  const parsed = (0, _sessionKeyUtils8PXPWO4Z.o)(canonicalKey);
  if (parsed?.agentId) return (0, _sessionKeyC0K0uhmG.c)(parsed.agentId);
  return resolveDefaultStoreAgentId(cfg);
}
function resolveStoredSessionKeyForAgentStore(params) {
  const raw = (0, _stringCoerceBje8XVt.c)(params.sessionKey) ?? "";
  if (!raw) return raw;
  const lowered = (0, _stringCoerceBje8XVt.a)(raw);
  if (lowered === "global" || lowered === "unknown") return lowered;
  const key = (0, _sessionKeyUtils8PXPWO4Z.o)(raw) ? raw : canonicalizeSessionKeyForAgent(params.agentId, raw);
  return resolveSessionStoreKey({
    cfg: params.cfg,
    sessionKey: key,
    storeAgentId: params.agentId
  });
}
function resolveStoredSessionOwnerAgentId(params) {
  const canonicalKey = resolveStoredSessionKeyForAgentStore(params);
  if (canonicalKey === "global" || canonicalKey === "unknown") return null;
  return resolveSessionStoreAgentId(params.cfg, canonicalKey);
}
function canonicalizeSpawnedByForAgent(cfg, agentId, spawnedBy) {
  const raw = (0, _stringCoerceBje8XVt.c)(spawnedBy) ?? "";
  if (!raw) return;
  const lower = (0, _stringCoerceBje8XVt.a)(raw);
  if (lower === "global" || lower === "unknown") return lower;
  let result;
  if (lower.startsWith("agent:")) result = lower;else
  result = `agent:${(0, _sessionKeyC0K0uhmG.c)(agentId)}:${lower}`;
  const parsed = (0, _sessionKeyUtils8PXPWO4Z.o)(result);
  return (0, _mainSessionC7L7pyed.t)({
    cfg,
    agentId: parsed?.agentId ? (0, _sessionKeyC0K0uhmG.c)(parsed.agentId) : agentId,
    sessionKey: result
  });
}
//#endregion
//#region src/config/sessions/combined-store-gateway.ts
function isStorePathTemplate(store) {
  return typeof store === "string" && store.includes("{agentId}");
}
function mergeSessionEntryIntoCombined(params) {
  const { cfg, combined, entry, agentId, canonicalKey } = params;
  const existing = combined[canonicalKey];
  if (existing && (existing.updatedAt ?? 0) > (entry.updatedAt ?? 0)) {
    const spawnedBy = canonicalizeSpawnedByForAgent(cfg, agentId, existing.spawnedBy ?? entry.spawnedBy);
    combined[canonicalKey] = {
      ...entry,
      ...existing,
      spawnedBy
    };
    return;
  }
  const spawnedBy = canonicalizeSpawnedByForAgent(cfg, agentId, entry.spawnedBy ?? existing?.spawnedBy);
  if (!existing && entry.spawnedBy === spawnedBy) combined[canonicalKey] = entry;else
  combined[canonicalKey] = {
    ...existing,
    ...entry,
    spawnedBy
  };
}
function loadCombinedSessionStoreForGateway(cfg, opts = {}) {
  const storeConfig = cfg.session?.store;
  if (storeConfig && !isStorePathTemplate(storeConfig)) {
    const storePath = (0, _pathsDG09LEN.d)(storeConfig);
    const defaultAgentId = (0, _sessionKeyC0K0uhmG.c)((0, _agentScopeB6RIBoEj.S)(cfg));
    const store = (0, _storeLoadDjtlQRVG.t)(storePath, { clone: false });
    const combined = {};
    for (const [key, entry] of Object.entries(store)) mergeSessionEntryIntoCombined({
      cfg,
      combined,
      entry,
      agentId: defaultAgentId,
      canonicalKey: resolveStoredSessionKeyForAgentStore({
        cfg,
        agentId: defaultAgentId,
        sessionKey: key
      })
    });
    return {
      storePath,
      store: combined
    };
  }
  const requestedAgentId = typeof opts.agentId === "string" && opts.agentId.trim() ? (0, _sessionKeyC0K0uhmG.c)(opts.agentId) : void 0;
  const targets = requestedAgentId ? (0, _targetsDjI6H8v.t)(cfg, requestedAgentId) : (0, _targetsDjI6H8v.r)(cfg);
  const combined = {};
  for (const target of targets) {
    const agentId = target.agentId;
    const storePath = target.storePath;
    const store = (0, _storeLoadDjtlQRVG.t)(storePath, { clone: false });
    for (const [key, entry] of Object.entries(store)) mergeSessionEntryIntoCombined({
      cfg,
      combined,
      entry,
      agentId,
      canonicalKey: resolveStoredSessionKeyForAgentStore({
        cfg,
        agentId,
        sessionKey: key
      })
    });
  }
  return {
    storePath: targets.length === 1 ? targets[0].storePath : typeof storeConfig === "string" && storeConfig.trim() ? storeConfig.trim() : "(multiple)",
    store: combined
  };
}
//#endregion /* v9-53a07d6e7ec12c63 */
