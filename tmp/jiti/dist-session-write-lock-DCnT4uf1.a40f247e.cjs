"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = drainSessionWriteLockStateForTest;exports.c = resolveSessionWriteLockAcquireTimeoutMs;exports.i = cleanStaleLockFiles;exports.n = void 0;exports.o = resetSessionWriteLockStateForTest;exports.r = acquireSessionWriteLock;exports.s = resolveSessionLockMaxHoldFromTimeout;exports.t = void 0;var _pidAliveTZpWSA3E = require("./pid-alive-TZpWSA3E.js");
var _processScopedMap0OBaOKV = require("./process-scoped-map-0OBaOKV5.js");
var _sessionWriteLockError_QNDHwhW = require("./session-write-lock-error-_QNDHwhW.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));
var _promises = _interopRequireDefault(require("node:fs/promises"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/agents/session-write-lock.ts
function isValidLockNumber(value) {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}
const CLEANUP_SIGNALS = [
"SIGINT",
"SIGTERM",
"SIGQUIT",
"SIGABRT"];

const CLEANUP_STATE_KEY = Symbol.for("openclaw.sessionWriteLockCleanupState");
const HELD_LOCKS_KEY = Symbol.for("openclaw.sessionWriteLockHeldLocks");
const WATCHDOG_STATE_KEY = Symbol.for("openclaw.sessionWriteLockWatchdogState");
const DEFAULT_STALE_MS = 1800 * 1e3;
const DEFAULT_MAX_HOLD_MS = 300 * 1e3;
const DEFAULT_SESSION_WRITE_LOCK_ACQUIRE_TIMEOUT_MS = exports.t = 6e4;
const DEFAULT_WATCHDOG_INTERVAL_MS = 6e4;
const DEFAULT_TIMEOUT_GRACE_MS = 120 * 1e3;
const ORPHAN_LOCK_PAYLOAD_GRACE_MS = 5e3;
const MAX_LOCK_HOLD_MS = 2147e6;
const HELD_LOCKS = (0, _processScopedMap0OBaOKV.t)(HELD_LOCKS_KEY);
function resolveSessionWriteLockAcquireTimeoutMs(config) {
  return resolvePositiveMs(config?.session?.writeLock?.acquireTimeoutMs, DEFAULT_SESSION_WRITE_LOCK_ACQUIRE_TIMEOUT_MS, { allowInfinity: true });
}
function resolveCleanupState() {
  const proc = process;
  if (!proc[CLEANUP_STATE_KEY]) proc[CLEANUP_STATE_KEY] = {
    registered: false,
    exitHandler: void 0,
    cleanupHandlers: /* @__PURE__ */new Map()
  };
  return proc[CLEANUP_STATE_KEY];
}
function resolveWatchdogState() {
  const proc = process;
  if (!proc[WATCHDOG_STATE_KEY]) proc[WATCHDOG_STATE_KEY] = {
    started: false,
    intervalMs: DEFAULT_WATCHDOG_INTERVAL_MS
  };
  return proc[WATCHDOG_STATE_KEY];
}
function resolvePositiveMs(value, fallback, opts = {}) {
  if (typeof value !== "number" || Number.isNaN(value) || value <= 0) return fallback;
  if (value === Number.POSITIVE_INFINITY) return opts.allowInfinity ? value : fallback;
  if (!Number.isFinite(value)) return fallback;
  return value;
}
function resolveSessionLockMaxHoldFromTimeout(params) {
  const minMs = resolvePositiveMs(params.minMs, DEFAULT_MAX_HOLD_MS);
  const timeoutMs = resolvePositiveMs(params.timeoutMs, minMs, { allowInfinity: true });
  if (timeoutMs === Number.POSITIVE_INFINITY) return MAX_LOCK_HOLD_MS;
  const graceMs = resolvePositiveMs(params.graceMs, DEFAULT_TIMEOUT_GRACE_MS);
  return Math.min(MAX_LOCK_HOLD_MS, Math.max(minMs, timeoutMs + graceMs));
}
async function releaseHeldLock(normalizedSessionFile, held, opts = {}) {
  if (HELD_LOCKS.get(normalizedSessionFile) !== held) return false;
  if (opts.force) held.count = 0;else
  {
    held.count -= 1;
    if (held.count > 0) return false;
  }
  if (held.releasePromise) {
    await held.releasePromise.catch(() => void 0);
    return true;
  }
  HELD_LOCKS.delete(normalizedSessionFile);
  held.releasePromise = (async () => {
    try {
      await held.handle.close();
    } catch {}
    try {
      await _promises.default.rm(held.lockPath, { force: true });
    } catch {}
  })();
  try {
    await held.releasePromise;
    return true;
  } finally {
    held.releasePromise = void 0;
    if (HELD_LOCKS.size === 0) stopWatchdogTimer();
  }
}
/**
* Synchronously release all held locks.
* Used during process exit when async operations aren't reliable.
*/
function releaseAllLocksSync() {
  for (const [sessionFile, held] of HELD_LOCKS) {
    closeFileHandleSyncBestEffort(held.handle);
    try {
      _nodeFs.default.rmSync(held.lockPath, { force: true });
    } catch {}
    HELD_LOCKS.delete(sessionFile);
  }
  if (HELD_LOCKS.size === 0) stopWatchdogTimer();
}
function closeFileHandleSyncBestEffort(handle) {
  const syncCloseSymbol = Object.getOwnPropertySymbols(Object.getPrototypeOf(handle)).find((symbol) => symbol.description === "kCloseSync");
  if (syncCloseSymbol) {
    const closeSync = handle[syncCloseSymbol];
    if (typeof closeSync === "function") try {
      closeSync.call(handle);
      return;
    } catch {}
  }
  handle.close().catch(() => void 0);
}
async function runLockWatchdogCheck(nowMs = Date.now()) {
  let released = 0;
  for (const [sessionFile, held] of HELD_LOCKS.entries()) {
    const heldForMs = nowMs - held.acquiredAt;
    if (heldForMs <= held.maxHoldMs) continue;
    process.stderr.write(`[session-write-lock] releasing lock held for ${heldForMs}ms (max=${held.maxHoldMs}ms): ${held.lockPath}\n`);
    if (await releaseHeldLock(sessionFile, held, { force: true })) released += 1;
  }
  return released;
}
function stopWatchdogTimer() {
  const watchdogState = resolveWatchdogState();
  if (watchdogState.timer) {
    clearInterval(watchdogState.timer);
    watchdogState.timer = void 0;
  }
  watchdogState.started = false;
}
function shouldStartBackgroundWatchdog() {
  return process.env.VITEST !== "true" || process.env.OPENCLAW_TEST_SESSION_LOCK_WATCHDOG === "1";
}
function ensureWatchdogStarted(intervalMs) {
  if (!shouldStartBackgroundWatchdog()) return;
  const watchdogState = resolveWatchdogState();
  if (watchdogState.started) return;
  watchdogState.started = true;
  watchdogState.intervalMs = intervalMs;
  watchdogState.timer = setInterval(() => {
    runLockWatchdogCheck().catch(() => {});
  }, intervalMs);
  watchdogState.timer.unref?.();
}
function handleTerminationSignal(signal) {
  releaseAllLocksSync();
  const cleanupState = resolveCleanupState();
  if (process.listenerCount(signal) === 1) {
    const handler = cleanupState.cleanupHandlers.get(signal);
    if (handler) {
      process.off(signal, handler);
      cleanupState.cleanupHandlers.delete(signal);
    }
    try {
      process.kill(process.pid, signal);
    } catch {}
  }
}
function registerCleanupHandlers() {
  const cleanupState = resolveCleanupState();
  cleanupState.registered = true;
  if (!cleanupState.exitHandler) {
    cleanupState.exitHandler = () => {
      releaseAllLocksSync();
    };
    process.on("exit", cleanupState.exitHandler);
  }
  ensureWatchdogStarted(DEFAULT_WATCHDOG_INTERVAL_MS);
  for (const signal of CLEANUP_SIGNALS) {
    if (cleanupState.cleanupHandlers.has(signal)) continue;
    try {
      const handler = () => handleTerminationSignal(signal);
      cleanupState.cleanupHandlers.set(signal, handler);
      process.on(signal, handler);
    } catch {}
  }
}
function unregisterCleanupHandlers() {
  const cleanupState = resolveCleanupState();
  if (cleanupState.exitHandler) {
    process.off("exit", cleanupState.exitHandler);
    cleanupState.exitHandler = void 0;
  }
  for (const [signal, handler] of cleanupState.cleanupHandlers) process.off(signal, handler);
  cleanupState.cleanupHandlers.clear();
  cleanupState.registered = false;
}
async function readLockPayload(lockPath) {
  try {
    const raw = await _promises.default.readFile(lockPath, "utf8");
    const parsed = JSON.parse(raw);
    const payload = {};
    if (isValidLockNumber(parsed.pid) && parsed.pid > 0) payload.pid = parsed.pid;
    if (typeof parsed.createdAt === "string") payload.createdAt = parsed.createdAt;
    if (isValidLockNumber(parsed.starttime)) payload.starttime = parsed.starttime;
    return payload;
  } catch {
    return null;
  }
}
async function resolveNormalizedSessionFile(sessionFile) {
  const resolvedSessionFile = _nodePath.default.resolve(sessionFile);
  const sessionDir = _nodePath.default.dirname(resolvedSessionFile);
  try {
    const normalizedDir = await _promises.default.realpath(sessionDir);
    return _nodePath.default.join(normalizedDir, _nodePath.default.basename(resolvedSessionFile));
  } catch {
    return resolvedSessionFile;
  }
}
function inspectLockPayload(payload, staleMs, nowMs) {
  const pid = isValidLockNumber(payload?.pid) && payload.pid > 0 ? payload.pid : null;
  const pidAlive = pid !== null ? (0, _pidAliveTZpWSA3E.n)(pid) : false;
  const createdAt = typeof payload?.createdAt === "string" ? payload.createdAt : null;
  const createdAtMs = createdAt ? Date.parse(createdAt) : NaN;
  const ageMs = Number.isFinite(createdAtMs) ? Math.max(0, nowMs - createdAtMs) : null;
  const storedStarttime = isValidLockNumber(payload?.starttime) ? payload.starttime : null;
  const pidRecycled = pidAlive && pid !== null && storedStarttime !== null ? (() => {
    const currentStarttime = (0, _pidAliveTZpWSA3E.t)(pid);
    return currentStarttime !== null && currentStarttime !== storedStarttime;
  })() : false;
  const staleReasons = [];
  if (pid === null) staleReasons.push("missing-pid");else
  if (!pidAlive) staleReasons.push("dead-pid");else
  if (pidRecycled) staleReasons.push("recycled-pid");
  if (ageMs === null) staleReasons.push("invalid-createdAt");else
  if (ageMs > staleMs) staleReasons.push("too-old");
  return {
    pid,
    pidAlive,
    createdAt,
    ageMs,
    stale: staleReasons.length > 0,
    staleReasons
  };
}
function lockInspectionNeedsMtimeStaleFallback(details) {
  return details.stale && details.staleReasons.every((reason) => reason === "missing-pid" || reason === "invalid-createdAt");
}
async function shouldReclaimContendedLockFile(lockPath, details, staleMs, nowMs) {
  if (!details.stale) return false;
  if (!lockInspectionNeedsMtimeStaleFallback(details)) return true;
  try {
    const stat = await _promises.default.stat(lockPath);
    return Math.max(0, nowMs - stat.mtimeMs) > Math.min(staleMs, ORPHAN_LOCK_PAYLOAD_GRACE_MS);
  } catch (error) {
    return error?.code !== "ENOENT";
  }
}
function shouldTreatAsOrphanSelfLock(params) {
  if ((isValidLockNumber(params.payload?.pid) ? params.payload.pid : null) !== process.pid) return false;
  if (HELD_LOCKS.has(params.normalizedSessionFile)) return false;
  const storedStarttime = isValidLockNumber(params.payload?.starttime) ? params.payload.starttime : null;
  if (storedStarttime === null) return params.reclaimLockWithoutStarttime;
  const currentStarttime = (0, _pidAliveTZpWSA3E.t)(process.pid);
  return currentStarttime !== null && currentStarttime === storedStarttime;
}
function inspectLockPayloadForSession(params) {
  const inspected = inspectLockPayload(params.payload, params.staleMs, params.nowMs);
  if (!shouldTreatAsOrphanSelfLock({
    payload: params.payload,
    normalizedSessionFile: params.normalizedSessionFile,
    reclaimLockWithoutStarttime: params.reclaimLockWithoutStarttime
  })) return inspected;
  return {
    ...inspected,
    stale: true,
    staleReasons: inspected.staleReasons.includes("orphan-self-pid") ? inspected.staleReasons : [...inspected.staleReasons, "orphan-self-pid"]
  };
}
async function cleanStaleLockFiles(params) {
  const sessionsDir = _nodePath.default.resolve(params.sessionsDir);
  const staleMs = resolvePositiveMs(params.staleMs, DEFAULT_STALE_MS);
  const removeStale = params.removeStale !== false;
  const nowMs = params.nowMs ?? Date.now();
  let entries = [];
  try {
    entries = await _promises.default.readdir(sessionsDir, { withFileTypes: true });
  } catch (err) {
    if (err.code === "ENOENT") return {
      locks: [],
      cleaned: []
    };
    throw err;
  }
  const locks = [];
  const cleaned = [];
  const lockEntries = entries.filter((entry) => entry.name.endsWith(".jsonl.lock")).toSorted((a, b) => a.name.localeCompare(b.name));
  for (const entry of lockEntries) {
    const lockPath = _nodePath.default.join(sessionsDir, entry.name);
    const lockInfo = {
      lockPath,
      ...inspectLockPayloadForSession({
        payload: await readLockPayload(lockPath),
        staleMs,
        nowMs,
        normalizedSessionFile: await resolveNormalizedSessionFile(lockPath.slice(0, -5)),
        reclaimLockWithoutStarttime: false
      }),
      removed: false
    };
    if (lockInfo.stale && removeStale) {
      await _promises.default.rm(lockPath, { force: true });
      lockInfo.removed = true;
      cleaned.push(lockInfo);
      params.log?.warn?.(`removed stale session lock: ${lockPath} (${lockInfo.staleReasons.join(", ") || "unknown"})`);
    }
    locks.push(lockInfo);
  }
  return {
    locks,
    cleaned
  };
}
async function acquireSessionWriteLock(params) {
  registerCleanupHandlers();
  const allowReentrant = params.allowReentrant ?? false;
  const timeoutMs = resolvePositiveMs(params.timeoutMs, resolveSessionWriteLockAcquireTimeoutMs(), { allowInfinity: true });
  const staleMs = resolvePositiveMs(params.staleMs, DEFAULT_STALE_MS);
  const maxHoldMs = resolvePositiveMs(params.maxHoldMs, DEFAULT_MAX_HOLD_MS);
  const sessionFile = _nodePath.default.resolve(params.sessionFile);
  const sessionDir = _nodePath.default.dirname(sessionFile);
  await _promises.default.mkdir(sessionDir, { recursive: true });
  const normalizedSessionFile = await resolveNormalizedSessionFile(sessionFile);
  const lockPath = `${normalizedSessionFile}.lock`;
  const held = HELD_LOCKS.get(normalizedSessionFile);
  if (allowReentrant && held) {
    held.count += 1;
    return { release: async () => {
        await releaseHeldLock(normalizedSessionFile, held);
      } };
  }
  const startedAt = Date.now();
  let attempt = 0;
  while (Date.now() - startedAt < timeoutMs) {
    attempt += 1;
    let handle = null;
    try {
      handle = await _promises.default.open(lockPath, "wx");
      const createdHeld = {
        count: 1,
        handle,
        lockPath,
        acquiredAt: Date.now(),
        maxHoldMs
      };
      HELD_LOCKS.set(normalizedSessionFile, createdHeld);
      const createdAt = (/* @__PURE__ */new Date()).toISOString();
      const starttime = (0, _pidAliveTZpWSA3E.t)(process.pid);
      const lockPayload = {
        pid: process.pid,
        createdAt
      };
      if (starttime !== null) lockPayload.starttime = starttime;
      await handle.writeFile(JSON.stringify(lockPayload, null, 2), "utf8");
      return { release: async () => {
          await releaseHeldLock(normalizedSessionFile, createdHeld);
        } };
    } catch (err) {
      if (handle) {
        if (HELD_LOCKS.get(normalizedSessionFile)?.handle === handle) {
          HELD_LOCKS.delete(normalizedSessionFile);
          if (HELD_LOCKS.size === 0) stopWatchdogTimer();
        }
        try {
          await handle.close();
        } catch {}
        try {
          await _promises.default.rm(lockPath, { force: true });
        } catch {}
      }
      if (err.code !== "EEXIST") throw err;
      const payload = await readLockPayload(lockPath);
      const nowMs = Date.now();
      if (await shouldReclaimContendedLockFile(lockPath, inspectLockPayloadForSession({
        payload,
        staleMs,
        nowMs,
        normalizedSessionFile,
        reclaimLockWithoutStarttime: true
      }), staleMs, nowMs)) {
        await _promises.default.rm(lockPath, { force: true });
        continue;
      }
      const remainingMs = timeoutMs - (Date.now() - startedAt);
      if (remainingMs <= 0) break;
      const delay = Math.min(1e3, 50 * attempt, remainingMs);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  const payload = await readLockPayload(lockPath);
  throw new _sessionWriteLockError_QNDHwhW.t({
    timeoutMs,
    owner: typeof payload?.pid === "number" ? `pid=${payload.pid}` : "unknown",
    lockPath
  });
}
const __testing = exports.n = {
  cleanupSignals: [...CLEANUP_SIGNALS],
  handleTerminationSignal,
  releaseAllLocksSync,
  runLockWatchdogCheck
};
async function drainSessionWriteLockStateForTest() {
  for (const [sessionFile, held] of Array.from(HELD_LOCKS.entries())) await releaseHeldLock(sessionFile, held, { force: true }).catch(() => void 0);
  stopWatchdogTimer();
  unregisterCleanupHandlers();
}
function resetSessionWriteLockStateForTest() {
  releaseAllLocksSync();
  stopWatchdogTimer();
  unregisterCleanupHandlers();
}
//#endregion /* v9-588b9e3f008f2a80 */
