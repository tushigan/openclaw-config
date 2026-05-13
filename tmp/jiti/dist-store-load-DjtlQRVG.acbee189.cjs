"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.C = isCacheEnabled;exports.S = getFileStatSnapshot;exports._ = isSessionStoreCacheEnabled;exports.a = getActiveSessionMaintenanceWarning;exports.b = writeSessionStoreCache;exports.c = resolveMaintenanceConfigFromInput;exports.d = parseSessionThreadInfoFast;exports.f = resolveLoadedSessionThreadInfo;exports.g = getSerializedSessionStore;exports.h = dropSessionStoreObjectCache;exports.i = capEntryCount;exports.l = shouldRunSessionEntryMaintenance;exports.m = cloneSessionStoreRecord;exports.n = normalizeSessionStore;exports.o = isProtectedSessionMaintenanceEntry;exports.p = clearSessionStoreCaches;exports.r = resolveMaintenanceConfig;exports.s = pruneStaleEntries;exports.t = loadSessionStore;exports.u = parseSessionThreadInfo;exports.v = setSerializedSessionStore;exports.w = resolveCacheTtlMs;exports.x = createExpiringMapCache;exports.y = takeMutableSessionStoreCache;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _sessionKeyUtils8PXPWO4Z = require("./session-key-utils-8PXPWO4Z.js");
var _subsystemCxWoQXRD = require("./subsystem-CxWoQXRD.js");
var _ioE69J4lLI = require("./io-E69J4lLI.js");
var _zodSchemaCOgITMqv = require("./zod-schema-COgITMqv.js");
var _parseDurationCIsOpJPW = require("./parse-duration-CIsOpJPW.js");
var _parseFiniteNumberDwCDYUjR = require("./parse-finite-number-DwCDYUjR.js");
require("./config-Dq84uU6c.js");
var _deliveryContextSharedTofZwoN = require("./delivery-context.shared-tofZwoN5.js");
var _sessionConversation6JE9TRWs = require("./session-conversation-6JE9TRWs.js");
var _registryLoadedReadBaloxaH = require("./registry-loaded-read-BaloxaH0.js");
var _typesB6qmUh0I = require("./types-B6qmUh0I.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/config/cache-utils.ts
function resolveCacheTtlMs(params) {
  const { envValue, defaultTtlMs } = params;
  if (envValue) {
    const parsed = (0, _parseFiniteNumberDwCDYUjR.r)(envValue);
    if (parsed !== void 0) return parsed;
  }
  return defaultTtlMs;
}
function isCacheEnabled(ttlMs) {
  return ttlMs > 0;
}
function resolveCacheNumeric(value) {
  return typeof value === "function" ? value() : value;
}
function resolvePruneIntervalMs(ttlMs, pruneIntervalMs) {
  if (typeof pruneIntervalMs === "function") return Math.max(0, Math.floor(pruneIntervalMs(ttlMs)));
  if (typeof pruneIntervalMs === "number") return Math.max(0, Math.floor(pruneIntervalMs));
  return ttlMs;
}
function isCacheEntryExpired(storedAt, now, ttlMs) {
  return now - storedAt > ttlMs;
}
function createExpiringMapCache(options) {
  const cache = /* @__PURE__ */new Map();
  const now = options.clock ?? Date.now;
  let lastPruneAt = 0;
  function getTtlMs() {
    return Math.max(0, Math.floor(resolveCacheNumeric(options.ttlMs)));
  }
  function maybePruneExpiredEntries(nowMs, ttlMs) {
    if (!isCacheEnabled(ttlMs)) return;
    if (nowMs - lastPruneAt < resolvePruneIntervalMs(ttlMs, options.pruneIntervalMs)) return;
    for (const [key, entry] of cache.entries()) if (isCacheEntryExpired(entry.storedAt, nowMs, ttlMs)) cache.delete(key);
    lastPruneAt = nowMs;
  }
  return {
    get: (key) => {
      const ttlMs = getTtlMs();
      if (!isCacheEnabled(ttlMs)) return;
      const nowMs = now();
      maybePruneExpiredEntries(nowMs, ttlMs);
      const entry = cache.get(key);
      if (!entry) return;
      if (isCacheEntryExpired(entry.storedAt, nowMs, ttlMs)) {
        cache.delete(key);
        return;
      }
      return entry.value;
    },
    set: (key, value) => {
      const ttlMs = getTtlMs();
      if (!isCacheEnabled(ttlMs)) return;
      const nowMs = now();
      maybePruneExpiredEntries(nowMs, ttlMs);
      cache.set(key, {
        storedAt: nowMs,
        value
      });
    },
    delete: (key) => {
      cache.delete(key);
    },
    clear: () => {
      cache.clear();
      lastPruneAt = 0;
    },
    keys: () => [...cache.keys()],
    size: () => cache.size,
    pruneExpired: () => {
      const ttlMs = getTtlMs();
      if (!isCacheEnabled(ttlMs)) return;
      const nowMs = now();
      for (const [key, entry] of cache.entries()) if (isCacheEntryExpired(entry.storedAt, nowMs, ttlMs)) cache.delete(key);
      lastPruneAt = nowMs;
    }
  };
}
function getFileStatSnapshot(filePath) {
  try {
    const stats = _nodeFs.default.statSync(filePath);
    return {
      mtimeMs: stats.mtimeMs,
      sizeBytes: stats.size
    };
  } catch {
    return;
  }
}
//#endregion
//#region src/config/sessions/store-cache.ts
const DEFAULT_SESSION_STORE_TTL_MS = 45e3;
const SESSION_STORE_CACHE = createExpiringMapCache({ ttlMs: getSessionStoreTtl });
const SESSION_STORE_SERIALIZED_CACHE = /* @__PURE__ */new Map();
function cloneSessionStoreRecord(store, serialized) {
  return JSON.parse(serialized ?? JSON.stringify(store));
}
function getSessionStoreTtl() {
  return resolveCacheTtlMs({
    envValue: process.env.OPENCLAW_SESSION_CACHE_TTL_MS,
    defaultTtlMs: DEFAULT_SESSION_STORE_TTL_MS
  });
}
function isSessionStoreCacheEnabled() {
  return isCacheEnabled(getSessionStoreTtl());
}
function clearSessionStoreCaches() {
  SESSION_STORE_CACHE.clear();
  SESSION_STORE_SERIALIZED_CACHE.clear();
}
function invalidateSessionStoreCache(storePath) {
  SESSION_STORE_CACHE.delete(storePath);
  SESSION_STORE_SERIALIZED_CACHE.delete(storePath);
}
function getSerializedSessionStore(storePath) {
  return SESSION_STORE_SERIALIZED_CACHE.get(storePath);
}
function setSerializedSessionStore(storePath, serialized) {
  if (serialized === void 0) {
    SESSION_STORE_SERIALIZED_CACHE.delete(storePath);
    return;
  }
  SESSION_STORE_SERIALIZED_CACHE.set(storePath, serialized);
}
function dropSessionStoreObjectCache(storePath) {
  SESSION_STORE_CACHE.delete(storePath);
}
function readSessionStoreCache(params) {
  const cached = SESSION_STORE_CACHE.get(params.storePath);
  if (!cached) return null;
  if (params.mtimeMs !== cached.mtimeMs || params.sizeBytes !== cached.sizeBytes) {
    invalidateSessionStoreCache(params.storePath);
    return null;
  }
  if (params.clone === false) return cached.store;
  return cloneSessionStoreRecord(cached.store, cached.serialized);
}
function takeMutableSessionStoreCache(params) {
  const cached = SESSION_STORE_CACHE.get(params.storePath);
  if (!cached) return null;
  if (params.mtimeMs !== cached.mtimeMs || params.sizeBytes !== cached.sizeBytes) {
    invalidateSessionStoreCache(params.storePath);
    return null;
  }
  SESSION_STORE_CACHE.delete(params.storePath);
  return cached.store;
}
function writeSessionStoreCache(params) {
  SESSION_STORE_CACHE.set(params.storePath, {
    store: params.serialized === void 0 ? cloneSessionStoreRecord(params.store) : params.store,
    mtimeMs: params.mtimeMs,
    sizeBytes: params.sizeBytes,
    serialized: params.serialized
  });
  if (params.serialized !== void 0) SESSION_STORE_SERIALIZED_CACHE.set(params.storePath, params.serialized);
}
//#endregion
//#region src/channels/plugins/session-thread-info-loaded.ts
function resolveLoadedSessionConversationThreadInfo(sessionKey) {
  const raw = (0, _sessionKeyUtils8PXPWO4Z.s)(sessionKey);
  if (!raw) return null;
  const rawId = raw.rawId.trim();
  if (!rawId) return null;
  const resolved = (0, _registryLoadedReadBaloxaH.t)(raw.channel)?.messaging?.resolveSessionConversation?.({
    kind: raw.kind,
    rawId
  });
  if (!resolved?.id?.trim()) return null;
  const id = resolved.id.trim();
  const threadId = (0, _stringCoerceBje8XVt.c)(resolved.threadId);
  return {
    baseSessionKey: threadId ? `${raw.prefix}:${id}` : (0, _stringCoerceBje8XVt.c)(sessionKey),
    threadId
  };
}
function resolveLoadedSessionThreadInfo(sessionKey) {
  return resolveLoadedSessionConversationThreadInfo(sessionKey) ?? (0, _sessionKeyUtils8PXPWO4Z.c)(sessionKey);
}
//#endregion
//#region src/config/sessions/thread-info.ts
/**
* Extract deliveryContext and threadId from a sessionKey.
* Supports generic :thread: suffixes plus plugin-owned thread/session grammars.
*/
function parseSessionThreadInfo(sessionKey) {
  return (0, _sessionConversation6JE9TRWs.i)(sessionKey);
}
function parseSessionThreadInfoFast(sessionKey) {
  return resolveLoadedSessionThreadInfo(sessionKey);
}
//#endregion
//#region src/config/sessions/store-maintenance.ts
const log$1 = (0, _subsystemCxWoQXRD.t)("sessions/store");
const DEFAULT_SESSION_PRUNE_AFTER_MS = 720 * 60 * 60 * 1e3;
const DEFAULT_SESSION_MAX_ENTRIES = 500;
const DEFAULT_SESSION_MAINTENANCE_MODE = "enforce";
const DEFAULT_SESSION_DISK_BUDGET_HIGH_WATER_RATIO = .8;
const STRICT_ENTRY_MAINTENANCE_MAX_ENTRIES = 49;
const MIN_BATCHED_ENTRY_MAINTENANCE_SLACK = 25;
const BATCHED_ENTRY_MAINTENANCE_SLACK_RATIO = .1;
function resolvePruneAfterMs(maintenance) {
  const normalized = (0, _stringCoerceBje8XVt.d)(maintenance?.pruneAfter ?? maintenance?.pruneDays);
  if (!normalized) return DEFAULT_SESSION_PRUNE_AFTER_MS;
  try {
    return (0, _parseDurationCIsOpJPW.t)(normalized, { defaultUnit: "d" });
  } catch {
    return DEFAULT_SESSION_PRUNE_AFTER_MS;
  }
}
function resolveResetArchiveRetentionMs(maintenance, pruneAfterMs) {
  const raw = maintenance?.resetArchiveRetention;
  if (raw === false) return null;
  const normalized = (0, _stringCoerceBje8XVt.d)(raw);
  if (!normalized) return pruneAfterMs;
  try {
    return (0, _parseDurationCIsOpJPW.t)(normalized, { defaultUnit: "d" });
  } catch {
    return pruneAfterMs;
  }
}
function resolveMaxDiskBytes(maintenance) {
  const raw = maintenance?.maxDiskBytes;
  const normalized = (0, _stringCoerceBje8XVt.d)(raw);
  if (!normalized) return null;
  try {
    return (0, _zodSchemaCOgITMqv.r)(normalized, { defaultUnit: "b" });
  } catch {
    return null;
  }
}
function resolveHighWaterBytes(maintenance, maxDiskBytes) {
  const computeDefault = () => {
    if (maxDiskBytes == null) return null;
    if (maxDiskBytes <= 0) return 0;
    return Math.max(1, Math.min(maxDiskBytes, Math.floor(maxDiskBytes * DEFAULT_SESSION_DISK_BUDGET_HIGH_WATER_RATIO)));
  };
  if (maxDiskBytes == null) return null;
  const raw = maintenance?.highWaterBytes;
  const normalized = (0, _stringCoerceBje8XVt.d)(raw);
  if (!normalized) return computeDefault();
  try {
    const parsed = (0, _zodSchemaCOgITMqv.r)(normalized, { defaultUnit: "b" });
    return Math.min(parsed, maxDiskBytes);
  } catch {
    return computeDefault();
  }
}
/**
* Resolve maintenance settings from openclaw.json (`session.maintenance`).
* Falls back to built-in defaults when config is missing or unset.
*/
function resolveMaintenanceConfigFromInput(maintenance) {
  const pruneAfterMs = resolvePruneAfterMs(maintenance);
  const maxDiskBytes = resolveMaxDiskBytes(maintenance);
  return {
    mode: maintenance?.mode ?? DEFAULT_SESSION_MAINTENANCE_MODE,
    pruneAfterMs,
    maxEntries: maintenance?.maxEntries ?? DEFAULT_SESSION_MAX_ENTRIES,
    resetArchiveRetentionMs: resolveResetArchiveRetentionMs(maintenance, pruneAfterMs),
    maxDiskBytes,
    highWaterBytes: resolveHighWaterBytes(maintenance, maxDiskBytes)
  };
}
function resolveSessionEntryMaintenanceHighWater(maxEntries) {
  if (!Number.isSafeInteger(maxEntries) || maxEntries <= 0) return 1;
  if (maxEntries <= STRICT_ENTRY_MAINTENANCE_MAX_ENTRIES) return maxEntries + 1;
  return maxEntries + Math.max(MIN_BATCHED_ENTRY_MAINTENANCE_SLACK, Math.ceil(maxEntries * BATCHED_ENTRY_MAINTENANCE_SLACK_RATIO));
}
function shouldRunSessionEntryMaintenance(params) {
  if (params.force) return true;
  return params.entryCount >= resolveSessionEntryMaintenanceHighWater(params.maxEntries);
}
/**
* Remove entries whose `updatedAt` is older than the configured threshold.
* Entries without `updatedAt` are kept (cannot determine staleness).
* Mutates `store` in-place.
*/
function pruneStaleEntries(store, overrideMaxAgeMs, opts = {}) {
  const maxAgeMs = overrideMaxAgeMs ?? resolveMaintenanceConfigFromInput().pruneAfterMs;
  const cutoffMs = Date.now() - maxAgeMs;
  let pruned = 0;
  for (const [key, entry] of Object.entries(store)) {
    if (shouldPreserveMaintenanceEntry({
      key,
      entry,
      preserveKeys: opts.preserveKeys
    })) continue;
    if (entry?.updatedAt != null && entry.updatedAt < cutoffMs) {
      opts.onPruned?.({
        key,
        entry
      });
      delete store[key];
      pruned++;
    }
  }
  if (pruned > 0 && opts.log !== false) log$1.info("pruned stale session entries", {
    pruned,
    maxAgeMs
  });
  return pruned;
}
function getEntryUpdatedAt(entry) {
  return entry?.updatedAt ?? Number.NEGATIVE_INFINITY;
}
function isSyntheticSessionMaintenanceKey(sessionKey) {
  const rest = (0, _stringCoerceBje8XVt.a)((0, _sessionKeyUtils8PXPWO4Z.o)(sessionKey)?.rest ?? sessionKey);
  return (0, _sessionKeyUtils8PXPWO4Z.a)(sessionKey) || (0, _sessionKeyUtils8PXPWO4Z.n)(sessionKey) || (0, _sessionKeyUtils8PXPWO4Z.i)(sessionKey) || rest.startsWith("hook:") || rest.startsWith("node:") || rest === "heartbeat" || rest.endsWith(":heartbeat") || rest.includes(":heartbeat:");
}
function isTelegramTopicSessionKey(sessionKey) {
  const rest = (0, _stringCoerceBje8XVt.a)((0, _sessionKeyUtils8PXPWO4Z.o)(sessionKey)?.rest ?? sessionKey);
  return /^telegram:(?:group|channel|direct|dm):.+:topic:[^:]+$/.test(rest);
}
function isExternalGroupOrChannelSessionKey(sessionKey) {
  const rest = (0, _stringCoerceBje8XVt.a)((0, _sessionKeyUtils8PXPWO4Z.o)(sessionKey)?.rest ?? sessionKey);
  return /^[^:]+:(?:group|channel):.+$/.test(rest);
}
function isProtectedSessionMaintenanceEntry(sessionKey, entry) {
  if (isSyntheticSessionMaintenanceKey(sessionKey)) return false;
  if (parseSessionThreadInfoFast(sessionKey).threadId) return true;
  if (isTelegramTopicSessionKey(sessionKey)) return true;
  if (isExternalGroupOrChannelSessionKey(sessionKey)) return true;
  const chatType = (0, _stringCoerceBje8XVt.a)(entry?.chatType ?? entry?.origin?.chatType);
  return chatType === "group" || chatType === "channel" || chatType === "thread";
}
function shouldPreserveMaintenanceEntry(params) {
  return params.preserveKeys?.has(params.key) === true || isProtectedSessionMaintenanceEntry(params.key, params.entry);
}
function getActiveSessionMaintenanceWarning(params) {
  const activeSessionKey = params.activeSessionKey.trim();
  if (!activeSessionKey) return null;
  const activeEntry = params.store[activeSessionKey];
  if (!activeEntry) return null;
  if (isProtectedSessionMaintenanceEntry(activeSessionKey, activeEntry)) return null;
  const cutoffMs = (params.nowMs ?? Date.now()) - params.pruneAfterMs;
  const wouldPrune = activeEntry.updatedAt != null ? activeEntry.updatedAt < cutoffMs : false;
  const keys = Object.keys(params.store);
  const wouldCap = wouldCapActiveSession({
    store: params.store,
    keys,
    activeEntry,
    activeSessionKey,
    maxEntries: params.maxEntries
  });
  if (!wouldPrune && !wouldCap) return null;
  return {
    activeSessionKey,
    activeUpdatedAt: activeEntry.updatedAt,
    totalEntries: keys.length,
    pruneAfterMs: params.pruneAfterMs,
    maxEntries: params.maxEntries,
    wouldPrune,
    wouldCap
  };
}
function wouldCapActiveSession(params) {
  if (params.keys.length <= params.maxEntries) return false;
  if (params.maxEntries <= 0) return true;
  const protectedCount = params.keys.filter((key) => key !== params.activeSessionKey && isProtectedSessionMaintenanceEntry(key, params.store[key])).length;
  const maxRemovableEntries = Math.max(0, params.maxEntries - protectedCount);
  if (maxRemovableEntries <= 0) return true;
  const activeUpdatedAt = getEntryUpdatedAt(params.activeEntry);
  let newerOrTieBeforeActive = 0;
  let seenActive = false;
  for (const key of params.keys) {
    if (key === params.activeSessionKey) {
      seenActive = true;
      continue;
    }
    if (isProtectedSessionMaintenanceEntry(key, params.store[key])) continue;
    const entryUpdatedAt = getEntryUpdatedAt(params.store[key]);
    if (entryUpdatedAt > activeUpdatedAt || !seenActive && entryUpdatedAt === activeUpdatedAt) {
      newerOrTieBeforeActive++;
      if (newerOrTieBeforeActive >= maxRemovableEntries) return true;
    }
  }
  return false;
}
/**
* Cap the store to the N most recently updated entries.
* Entries without `updatedAt` are sorted last (removed first when over limit).
* Mutates `store` in-place.
*/
function capEntryCount(store, overrideMax, opts = {}) {
  const maxEntries = overrideMax ?? resolveMaintenanceConfigFromInput().maxEntries;
  const preservedCount = Object.entries(store).filter(([key, entry]) => shouldPreserveMaintenanceEntry({
    key,
    entry,
    preserveKeys: opts.preserveKeys
  })).length;
  const maxRemovableEntries = Math.max(0, maxEntries - preservedCount);
  const keys = Object.keys(store).filter((key) => !shouldPreserveMaintenanceEntry({
    key,
    entry: store[key],
    preserveKeys: opts.preserveKeys
  }));
  if (keys.length <= maxRemovableEntries) return 0;
  const toRemove = keys.toSorted((a, b) => {
    const aTime = getEntryUpdatedAt(store[a]);
    return getEntryUpdatedAt(store[b]) - aTime;
  }).slice(maxRemovableEntries);
  for (const key of toRemove) {
    const entry = store[key];
    if (entry) opts.onCapped?.({
      key,
      entry
    });
    delete store[key];
  }
  if (opts.log !== false) log$1.info("capped session entry count", {
    removed: toRemove.length,
    maxEntries
  });
  return toRemove.length;
}
//#endregion
//#region src/config/sessions/store-maintenance-runtime.ts
function resolveMaintenanceConfig() {
  let maintenance;
  try {
    maintenance = (0, _ioE69J4lLI.i)().session?.maintenance;
  } catch {}
  return resolveMaintenanceConfigFromInput(maintenance);
}
//#endregion
//#region src/config/sessions/store-migrations.ts
function applySessionStoreMigrations(store) {
  let changed = false;
  for (const entry of Object.values(store)) {
    if (!entry || typeof entry !== "object") continue;
    const rec = entry;
    if (typeof rec.channel !== "string" && typeof rec.provider === "string") {
      rec.channel = rec.provider;
      delete rec.provider;
      changed = true;
    }
    if (typeof rec.lastChannel !== "string" && typeof rec.lastProvider === "string") {
      rec.lastChannel = rec.lastProvider;
      delete rec.lastProvider;
      changed = true;
    }
    if (typeof rec.groupChannel !== "string" && typeof rec.room === "string") {
      rec.groupChannel = rec.room;
      delete rec.room;
      changed = true;
    } else if ("room" in rec) {
      delete rec.room;
      changed = true;
    }
  }
  return changed;
}
//#endregion
//#region src/config/sessions/store-load.ts
const log = (0, _subsystemCxWoQXRD.t)("sessions/store");
function isSessionStoreRecord(value) {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
function normalizeSessionEntryDelivery(entry) {
  const normalized = (0, _deliveryContextSharedTofZwoN.a)({
    channel: entry.channel,
    lastChannel: entry.lastChannel,
    lastTo: entry.lastTo,
    lastAccountId: entry.lastAccountId,
    lastThreadId: entry.lastThreadId ?? entry.deliveryContext?.threadId ?? entry.origin?.threadId,
    deliveryContext: entry.deliveryContext
  });
  const nextDelivery = normalized.deliveryContext;
  const sameDelivery = (entry.deliveryContext?.channel ?? void 0) === nextDelivery?.channel && (entry.deliveryContext?.to ?? void 0) === nextDelivery?.to && (entry.deliveryContext?.accountId ?? void 0) === nextDelivery?.accountId && (entry.deliveryContext?.threadId ?? void 0) === nextDelivery?.threadId;
  const sameLast = entry.lastChannel === normalized.lastChannel && entry.lastTo === normalized.lastTo && entry.lastAccountId === normalized.lastAccountId && entry.lastThreadId === normalized.lastThreadId;
  if (sameDelivery && sameLast) return entry;
  return {
    ...entry,
    deliveryContext: nextDelivery,
    lastChannel: normalized.lastChannel,
    lastTo: normalized.lastTo,
    lastAccountId: normalized.lastAccountId,
    lastThreadId: normalized.lastThreadId
  };
}
function stripPersistedSkillsCache(entry) {
  const snapshot = entry.skillsSnapshot;
  if (!snapshot || snapshot.resolvedSkills === void 0) return entry;
  const { resolvedSkills: _drop, ...rest } = snapshot;
  return {
    ...entry,
    skillsSnapshot: rest
  };
}
function normalizeSessionStore(store) {
  let changed = false;
  for (const [key, entry] of Object.entries(store)) {
    if (!entry) continue;
    const normalized = stripPersistedSkillsCache(normalizeSessionEntryDelivery((0, _typesB6qmUh0I.a)(entry)));
    if (normalized !== entry) {
      store[key] = normalized;
      changed = true;
    }
  }
  return changed;
}
function loadSessionStore(storePath, opts = {}) {
  if (!opts.skipCache && isSessionStoreCacheEnabled()) {
    const currentFileStat = getFileStatSnapshot(storePath);
    const cached = readSessionStoreCache({
      storePath,
      mtimeMs: currentFileStat?.mtimeMs,
      sizeBytes: currentFileStat?.sizeBytes,
      clone: opts.clone
    });
    if (cached) return cached;
  }
  let store = {};
  let fileStat = getFileStatSnapshot(storePath);
  let mtimeMs = fileStat?.mtimeMs;
  let serializedFromDisk;
  const maxReadAttempts = process.platform === "win32" ? 3 : 1;
  const retryBuf = maxReadAttempts > 1 ? new Int32Array(new SharedArrayBuffer(4)) : void 0;
  for (let attempt = 0; attempt < maxReadAttempts; attempt += 1) try {
    const raw = _nodeFs.default.readFileSync(storePath, "utf-8");
    if (raw.length === 0 && attempt < maxReadAttempts - 1) {
      Atomics.wait(retryBuf, 0, 0, 50);
      continue;
    }
    const parsed = JSON.parse(raw);
    if (isSessionStoreRecord(parsed)) {
      store = parsed;
      serializedFromDisk = raw;
    }
    fileStat = getFileStatSnapshot(storePath) ?? fileStat;
    mtimeMs = fileStat?.mtimeMs;
    break;
  } catch {
    if (attempt < maxReadAttempts - 1) {
      Atomics.wait(retryBuf, 0, 0, 50);
      continue;
    }
  }
  const migrated = applySessionStoreMigrations(store);
  const normalized = normalizeSessionStore(store);
  if (migrated || normalized) serializedFromDisk = void 0;
  if (opts.runMaintenance) {
    const maintenance = opts.maintenanceConfig ?? resolveMaintenanceConfig();
    const beforeCount = Object.keys(store).length;
    if (maintenance.mode === "enforce" && beforeCount > maintenance.maxEntries) {
      const pruned = pruneStaleEntries(store, maintenance.pruneAfterMs, { log: false });
      const countAfterPrune = Object.keys(store).length;
      const capped = shouldRunSessionEntryMaintenance({
        entryCount: countAfterPrune,
        maxEntries: maintenance.maxEntries
      }) ? capEntryCount(store, maintenance.maxEntries, { log: false }) : 0;
      const afterCount = Object.keys(store).length;
      if (pruned > 0 || capped > 0) {
        serializedFromDisk = void 0;
        log.info("applied load-time maintenance to oversized session store", {
          storePath,
          before: beforeCount,
          after: afterCount,
          pruned,
          capped,
          maxEntries: maintenance.maxEntries
        });
      }
    }
  }
  setSerializedSessionStore(storePath, serializedFromDisk);
  if (!opts.skipCache && isSessionStoreCacheEnabled()) writeSessionStoreCache({
    storePath,
    store,
    mtimeMs,
    sizeBytes: fileStat?.sizeBytes,
    serialized: serializedFromDisk
  });
  return opts.clone === false ? store : cloneSessionStoreRecord(store, serializedFromDisk);
}
//#endregion /* v9-da6a4757952ed81b */
