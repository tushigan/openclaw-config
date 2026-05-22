"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = resolveAllowFromAccountId;exports.c = safeChannelKey;exports.i = readAllowFromFileWithExists;exports.l = setAllowFromFileReadCache;exports.n = dedupePreserveOrder;exports.o = resolveAllowFromFilePath;exports.r = readAllowFromFileSyncWithExists;exports.s = resolvePairingCredentialsDir;exports.t = clearAllowFromFileReadCacheForNamespace;exports.u = shouldIncludeLegacyAllowFromEntries;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _homeDirG5LU3LmA = require("./home-dir-g5LU3LmA.js");
var _pathsC1_Y0cDn = require("./paths-C1_Y0cDn.js");
require("./account-id-Bj7l9NI7.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));
var _nodeOs = _interopRequireDefault(require("node:os"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/pairing/allow-from-store-file.ts
const allowFromReadCache = /* @__PURE__ */new Map();
function resolvePairingCredentialsDir(env = process.env) {
  return (0, _pathsC1_Y0cDn.g)(env, (0, _pathsC1_Y0cDn.v)(env, () => (0, _homeDirG5LU3LmA.o)(env, _nodeOs.default.homedir)));
}
function describePairingFilenameKeyInput(value) {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed ? `string length ${trimmed.length}` : "empty string";
  }
  if (typeof value === "number" && !Number.isFinite(value)) return "non-finite number";
  return typeof value;
}
function invalidPairingFilenameKeyError(kind, reason, value) {
  return /* @__PURE__ */new Error(`invalid pairing ${kind}: ${reason}; got ${describePairingFilenameKeyInput(value)}`);
}
function normalizePairingFilenameKey(value, kind) {
  if (typeof value !== "string") throw invalidPairingFilenameKeyError(kind, "expected non-empty string", value);
  const raw = (0, _stringCoerceBje8XVt.a)(value);
  if (!raw) throw invalidPairingFilenameKeyError(kind, "expected non-empty string", value);
  const safe = raw.replace(/[\\/:*?"<>|]/g, "_").replace(/\.\./g, "_");
  if (!safe || safe === "_") throw invalidPairingFilenameKeyError(kind, "sanitized filename key is empty", value);
  return safe;
}
/** Sanitize channel ID for use in filenames (prevent path traversal). */
function safeChannelKey(channel) {
  return normalizePairingFilenameKey(channel, "channel");
}
function safeAccountKey(accountId) {
  return normalizePairingFilenameKey(accountId, "account id");
}
function resolveOptionalAccountFilenameKey(accountId) {
  if (accountId == null) return null;
  if (typeof accountId !== "string") throw invalidPairingFilenameKeyError("account id", "expected non-empty string", accountId);
  const normalizedAccountId = (0, _stringCoerceBje8XVt.c)(accountId) ?? "";
  return normalizedAccountId ? safeAccountKey(normalizedAccountId) : null;
}
function resolveAllowFromFilePath(channel, env = process.env, accountId) {
  const base = safeChannelKey(channel);
  const accountKey = resolveOptionalAccountFilenameKey(accountId);
  if (!accountKey) return _nodePath.default.join(resolvePairingCredentialsDir(env), `${base}-allowFrom.json`);
  return _nodePath.default.join(resolvePairingCredentialsDir(env), `${base}-${accountKey}-allowFrom.json`);
}
function dedupePreserveOrder(entries) {
  const seen = /* @__PURE__ */new Set();
  const out = [];
  for (const entry of entries) {
    const normalized = (0, _stringCoerceBje8XVt.c)(entry) ?? "";
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    out.push(normalized);
  }
  return out;
}
function shouldIncludeLegacyAllowFromEntries(normalizedAccountId) {
  return !normalizedAccountId || normalizedAccountId === "default";
}
function resolveAllowFromAccountId(accountId) {
  if (accountId != null && typeof accountId !== "string") throw invalidPairingFilenameKeyError("account id", "expected non-empty string", accountId);
  return (0, _stringCoerceBje8XVt.a)(accountId) || "default";
}
function cloneAllowFromCacheEntry(entry) {
  return {
    exists: entry.exists,
    mtimeMs: entry.mtimeMs,
    size: entry.size,
    entries: entry.entries.slice()
  };
}
function resolveAllowFromCacheKey(cacheNamespace, filePath) {
  return `${cacheNamespace}\u0000${filePath}`;
}
function setAllowFromFileReadCache(params) {
  allowFromReadCache.set(resolveAllowFromCacheKey(params.cacheNamespace, params.filePath), cloneAllowFromCacheEntry(params.entry));
}
function resolveAllowFromReadCacheHit(params) {
  const cached = allowFromReadCache.get(resolveAllowFromCacheKey(params.cacheNamespace, params.filePath));
  if (!cached) return null;
  if (cached.exists !== params.exists) return null;
  if (!params.exists) return cloneAllowFromCacheEntry(cached);
  if (cached.mtimeMs !== params.mtimeMs || cached.size !== params.size) return null;
  return cloneAllowFromCacheEntry(cached);
}
function resolveAllowFromReadCacheOrMissing(params) {
  const cached = resolveAllowFromReadCacheHit({
    cacheNamespace: params.cacheNamespace,
    filePath: params.filePath,
    exists: Boolean(params.stat),
    mtimeMs: params.stat?.mtimeMs ?? null,
    size: params.stat?.size ?? null
  });
  if (cached) return {
    entries: cached.entries,
    exists: cached.exists
  };
  if (!params.stat) {
    setAllowFromFileReadCache({
      cacheNamespace: params.cacheNamespace,
      filePath: params.filePath,
      entry: {
        exists: false,
        mtimeMs: null,
        size: null,
        entries: []
      }
    });
    return {
      entries: [],
      exists: false
    };
  }
  return null;
}
async function readAllowFromFileWithExists(params) {
  let stat = null;
  try {
    stat = await _nodeFs.default.promises.stat(params.filePath);
  } catch (err) {
    if (err.code !== "ENOENT") throw err;
  }
  const cachedOrMissing = resolveAllowFromReadCacheOrMissing({
    cacheNamespace: params.cacheNamespace,
    filePath: params.filePath,
    stat
  });
  if (cachedOrMissing) return cachedOrMissing;
  if (!stat) return {
    entries: [],
    exists: false
  };
  let raw = "";
  try {
    raw = await _nodeFs.default.promises.readFile(params.filePath, "utf8");
  } catch (err) {
    if (err.code === "ENOENT") return {
      entries: [],
      exists: false
    };
    throw err;
  }
  let entries = [];
  try {
    entries = params.normalizeStore(JSON.parse(raw));
  } catch {
    entries = [];
  }
  setAllowFromFileReadCache({
    cacheNamespace: params.cacheNamespace,
    filePath: params.filePath,
    entry: {
      exists: true,
      mtimeMs: stat.mtimeMs,
      size: stat.size,
      entries
    }
  });
  return {
    entries,
    exists: true
  };
}
function readAllowFromFileSyncWithExists(params) {
  let stat = null;
  try {
    stat = _nodeFs.default.statSync(params.filePath);
  } catch (err) {
    if (err.code !== "ENOENT") throw err;
  }
  const cachedOrMissing = resolveAllowFromReadCacheOrMissing({
    cacheNamespace: params.cacheNamespace,
    filePath: params.filePath,
    stat
  });
  if (cachedOrMissing) return cachedOrMissing;
  if (!stat) return {
    entries: [],
    exists: false
  };
  let raw = "";
  try {
    raw = _nodeFs.default.readFileSync(params.filePath, "utf8");
  } catch (err) {
    if (err.code === "ENOENT") return {
      entries: [],
      exists: false
    };
    throw err;
  }
  try {
    const parsed = JSON.parse(raw);
    const entries = params.normalizeStore(parsed);
    setAllowFromFileReadCache({
      cacheNamespace: params.cacheNamespace,
      filePath: params.filePath,
      entry: {
        exists: true,
        mtimeMs: stat.mtimeMs,
        size: stat.size,
        entries
      }
    });
    return {
      entries,
      exists: true
    };
  } catch {
    setAllowFromFileReadCache({
      cacheNamespace: params.cacheNamespace,
      filePath: params.filePath,
      entry: {
        exists: true,
        mtimeMs: stat.mtimeMs,
        size: stat.size,
        entries: []
      }
    });
    return {
      entries: [],
      exists: true
    };
  }
}
function clearAllowFromFileReadCacheForNamespace(cacheNamespace) {
  for (const key of allowFromReadCache.keys()) if (key.startsWith(`${cacheNamespace}\u0000`)) allowFromReadCache.delete(key);
}
//#endregion /* v9-1bdc7a590fcfb098 */
