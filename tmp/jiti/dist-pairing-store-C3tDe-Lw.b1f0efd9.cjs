"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = readChannelAllowFromStore;exports.c = readLegacyChannelAllowFromStoreSync;exports.d = upsertChannelPairingRequest;exports.f = getPairingAdapter;exports.i = listChannelPairingRequests;exports.l = removeChannelAllowFromStoreEntry;exports.m = notifyPairingApproved;exports.n = approveChannelPairingCode;exports.o = readChannelAllowFromStoreSync;exports.p = listPairingChannels;exports.r = clearPairingAllowFromReadCacheForTest;exports.s = readLegacyChannelAllowFromStore;exports.t = addChannelAllowFromStoreEntry;exports.u = resolveChannelAllowFromPath;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
require("./account-id-Bj7l9NI7.js");
var _fileLockCqxhL0b = require("./file-lock-CqxhL0b-.js");
require("./file-lock-C8-Vkrrw.js");
var _registryBkuUNjzB = require("./registry-BkuUNjzB.js");
var _jsonStoreDB5orcJO = require("./json-store-DB5orcJO.js");
var _allowFromStoreFile0fkquIHc = require("./allow-from-store-file-0fkquIHc.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));
var _nodeCrypto = _interopRequireDefault(require("node:crypto"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/channels/plugins/pairing.ts
function listPairingChannels() {
  return (0, _registryBkuUNjzB.i)().filter((plugin) => plugin.pairing).map((plugin) => plugin.id);
}
function getPairingAdapter(channelId) {
  return (0, _registryBkuUNjzB.t)(channelId)?.pairing ?? null;
}
function requirePairingAdapter(channelId) {
  const adapter = getPairingAdapter(channelId);
  if (!adapter) throw new Error(`Channel ${channelId} does not support pairing`);
  return adapter;
}
async function notifyPairingApproved(params) {
  const adapter = params.pairingAdapter ?? requirePairingAdapter(params.channelId);
  if (!adapter.notifyApproval) return;
  await adapter.notifyApproval({
    cfg: params.cfg,
    id: params.id,
    runtime: params.runtime
  });
}
//#endregion
//#region src/pairing/pairing-store.ts
const PAIRING_CODE_LENGTH = 8;
const PAIRING_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
const PAIRING_CODE_MAX_ATTEMPTS = 500;
const PAIRING_PENDING_TTL_MS = 3600 * 1e3;
const PAIRING_PENDING_MAX = 3;
const PAIRING_STORE_LOCK_OPTIONS = {
  retries: {
    retries: 10,
    factor: 2,
    minTimeout: 100,
    maxTimeout: 1e4,
    randomize: true
  },
  stale: 3e4
};
const PAIRING_ALLOW_FROM_CACHE_NAMESPACE = "pairing-store";
function resolvePairingPath(channel, env = process.env) {
  return _nodePath.default.join((0, _allowFromStoreFile0fkquIHc.s)(env), `${(0, _allowFromStoreFile0fkquIHc.c)(channel)}-pairing.json`);
}
function resolveChannelAllowFromPath(channel, env = process.env, accountId) {
  return (0, _allowFromStoreFile0fkquIHc.o)(channel, env, accountId);
}
async function readJsonFile(filePath, fallback) {
  return await (0, _jsonStoreDB5orcJO.t)(filePath, fallback);
}
async function writeJsonFile(filePath, value) {
  await (0, _jsonStoreDB5orcJO.n)(filePath, value);
}
async function readPairingRequests(filePath) {
  const { value } = await readJsonFile(filePath, {
    version: 1,
    requests: []
  });
  return Array.isArray(value.requests) ? value.requests : [];
}
async function readPrunedPairingRequests(filePath) {
  return pruneExpiredRequests(await readPairingRequests(filePath), Date.now());
}
async function ensureJsonFile(filePath, fallback) {
  try {
    await _nodeFs.default.promises.access(filePath);
  } catch {
    await writeJsonFile(filePath, fallback);
  }
}
async function withFileLock(filePath, fallback, fn) {
  await ensureJsonFile(filePath, fallback);
  return await (0, _fileLockCqxhL0b.a)(filePath, PAIRING_STORE_LOCK_OPTIONS, async () => {
    return await fn();
  });
}
function parseTimestamp(value) {
  if (!value) return null;
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) return null;
  return parsed;
}
function isExpired(entry, nowMs) {
  const createdAt = parseTimestamp(entry.createdAt);
  if (!createdAt) return true;
  return nowMs - createdAt > PAIRING_PENDING_TTL_MS;
}
function pruneExpiredRequests(reqs, nowMs) {
  const kept = [];
  let removed = false;
  for (const req of reqs) {
    if (isExpired(req, nowMs)) {
      removed = true;
      continue;
    }
    kept.push(req);
  }
  return {
    requests: kept,
    removed
  };
}
function resolveLastSeenAt(entry) {
  return parseTimestamp(entry.lastSeenAt) ?? parseTimestamp(entry.createdAt) ?? 0;
}
function resolvePairingRequestAccountId(entry) {
  return normalizePairingAccountId(entry.meta?.accountId) || "default";
}
function pruneExcessRequestsByAccount(reqs, maxPending) {
  if (maxPending <= 0 || reqs.length <= maxPending) return {
    requests: reqs,
    removed: false
  };
  const grouped = /* @__PURE__ */new Map();
  for (const [index, entry] of reqs.entries()) {
    const accountId = resolvePairingRequestAccountId(entry);
    const current = grouped.get(accountId);
    if (current) {
      current.push(index);
      continue;
    }
    grouped.set(accountId, [index]);
  }
  const droppedIndexes = /* @__PURE__ */new Set();
  for (const indexes of grouped.values()) {
    if (indexes.length <= maxPending) continue;
    const sortedIndexes = indexes.slice().toSorted((left, right) => resolveLastSeenAt(reqs[left]) - resolveLastSeenAt(reqs[right]));
    for (const index of sortedIndexes.slice(0, sortedIndexes.length - maxPending)) droppedIndexes.add(index);
  }
  if (droppedIndexes.size === 0) return {
    requests: reqs,
    removed: false
  };
  return {
    requests: reqs.filter((_, index) => !droppedIndexes.has(index)),
    removed: true
  };
}
function randomCode() {
  let out = "";
  for (let i = 0; i < PAIRING_CODE_LENGTH; i++) {
    const idx = _nodeCrypto.default.randomInt(0, 32);
    out += PAIRING_CODE_ALPHABET[idx];
  }
  return out;
}
function generateUniqueCode(existing) {
  for (let attempt = 0; attempt < PAIRING_CODE_MAX_ATTEMPTS; attempt += 1) {
    const code = randomCode();
    if (!existing.has(code)) return code;
  }
  throw new Error(`failed to generate unique pairing code after ${PAIRING_CODE_MAX_ATTEMPTS} attempts; existing code count: ${existing.size}`);
}
function normalizePairingAccountId(accountId) {
  return (0, _stringCoerceBje8XVt.a)(accountId);
}
function requestMatchesAccountId(entry, normalizedAccountId) {
  if (!normalizedAccountId) return true;
  return resolvePairingRequestAccountId(entry) === normalizedAccountId;
}
function normalizeId(value) {
  return (0, _stringCoerceBje8XVt.d)(value) ?? "";
}
function normalizeAllowEntry(channel, entry) {
  const trimmed = entry.trim();
  if (!trimmed) return "";
  if (trimmed === "*") return "";
  const adapter = getPairingAdapter(channel);
  return (0, _stringCoerceBje8XVt.c)(adapter?.normalizeAllowEntry ? adapter.normalizeAllowEntry(trimmed) : trimmed) ?? "";
}
function normalizeAllowFromList(channel, store) {
  return (0, _allowFromStoreFile0fkquIHc.n)((Array.isArray(store.allowFrom) ? store.allowFrom : []).map((v) => normalizeAllowEntry(channel, v)).filter(Boolean));
}
function normalizeAllowFromInput(channel, entry) {
  return normalizeAllowEntry(channel, normalizeId(entry));
}
async function readAllowFromStateForPath(channel, filePath) {
  return (await readAllowFromStateForPathWithExists(channel, filePath)).entries;
}
async function readAllowFromStateForPathWithExists(channel, filePath) {
  return await (0, _allowFromStoreFile0fkquIHc.i)({
    cacheNamespace: PAIRING_ALLOW_FROM_CACHE_NAMESPACE,
    filePath,
    normalizeStore: (store) => normalizeAllowFromList(channel, store)
  });
}
function readAllowFromStateForPathSync(channel, filePath) {
  return readAllowFromStateForPathSyncWithExists(channel, filePath).entries;
}
function readAllowFromStateForPathSyncWithExists(channel, filePath) {
  return (0, _allowFromStoreFile0fkquIHc.r)({
    cacheNamespace: PAIRING_ALLOW_FROM_CACHE_NAMESPACE,
    filePath,
    normalizeStore: (store) => normalizeAllowFromList(channel, store)
  });
}
async function readAllowFromState(params) {
  const { value } = await readJsonFile(params.filePath, {
    version: 1,
    allowFrom: []
  });
  return {
    current: normalizeAllowFromList(params.channel, value),
    normalized: normalizeAllowFromInput(params.channel, params.entry) || null
  };
}
async function writeAllowFromState(filePath, allowFrom) {
  await writeJsonFile(filePath, {
    version: 1,
    allowFrom
  });
  let stat = null;
  try {
    stat = await _nodeFs.default.promises.stat(filePath);
  } catch (err) {
    if (err.code !== "ENOENT") throw err;
  }
  (0, _allowFromStoreFile0fkquIHc.l)({
    cacheNamespace: PAIRING_ALLOW_FROM_CACHE_NAMESPACE,
    filePath,
    entry: {
      exists: true,
      mtimeMs: stat?.mtimeMs ?? null,
      size: stat?.size ?? null,
      entries: allowFrom.slice()
    }
  });
}
async function readNonDefaultAccountAllowFrom(params) {
  const scopedPath = (0, _allowFromStoreFile0fkquIHc.o)(params.channel, params.env, params.accountId);
  return await readAllowFromStateForPath(params.channel, scopedPath);
}
function readNonDefaultAccountAllowFromSync(params) {
  const scopedPath = (0, _allowFromStoreFile0fkquIHc.o)(params.channel, params.env, params.accountId);
  return readAllowFromStateForPathSync(params.channel, scopedPath);
}
async function updateAllowFromStoreEntry(params) {
  const env = params.env ?? process.env;
  const filePath = (0, _allowFromStoreFile0fkquIHc.o)(params.channel, env, params.accountId);
  return await withFileLock(filePath, {
    version: 1,
    allowFrom: []
  }, async () => {
    const { current, normalized } = await readAllowFromState({
      channel: params.channel,
      entry: params.entry,
      filePath
    });
    if (!normalized) return {
      changed: false,
      allowFrom: current
    };
    const next = params.apply(current, normalized);
    if (!next) return {
      changed: false,
      allowFrom: current
    };
    await writeAllowFromState(filePath, next);
    return {
      changed: true,
      allowFrom: next
    };
  });
}
async function readLegacyChannelAllowFromStore(channel, env = process.env) {
  return await readAllowFromStateForPath(channel, (0, _allowFromStoreFile0fkquIHc.o)(channel, env));
}
async function readChannelAllowFromStore(channel, env = process.env, accountId) {
  const resolvedAccountId = (0, _allowFromStoreFile0fkquIHc.a)(accountId);
  if (!(0, _allowFromStoreFile0fkquIHc.u)(resolvedAccountId)) return await readNonDefaultAccountAllowFrom({
    channel,
    env,
    accountId: resolvedAccountId
  });
  const scopedEntries = await readAllowFromStateForPath(channel, (0, _allowFromStoreFile0fkquIHc.o)(channel, env, resolvedAccountId));
  const legacyEntries = await readAllowFromStateForPath(channel, (0, _allowFromStoreFile0fkquIHc.o)(channel, env));
  return (0, _allowFromStoreFile0fkquIHc.n)([...scopedEntries, ...legacyEntries]);
}
function readLegacyChannelAllowFromStoreSync(channel, env = process.env) {
  return readAllowFromStateForPathSync(channel, (0, _allowFromStoreFile0fkquIHc.o)(channel, env));
}
function readChannelAllowFromStoreSync(channel, env = process.env, accountId) {
  const resolvedAccountId = (0, _allowFromStoreFile0fkquIHc.a)(accountId);
  if (!(0, _allowFromStoreFile0fkquIHc.u)(resolvedAccountId)) return readNonDefaultAccountAllowFromSync({
    channel,
    env,
    accountId: resolvedAccountId
  });
  const scopedEntries = readAllowFromStateForPathSync(channel, (0, _allowFromStoreFile0fkquIHc.o)(channel, env, resolvedAccountId));
  const legacyEntries = readAllowFromStateForPathSync(channel, (0, _allowFromStoreFile0fkquIHc.o)(channel, env));
  return (0, _allowFromStoreFile0fkquIHc.n)([...scopedEntries, ...legacyEntries]);
}
function clearPairingAllowFromReadCacheForTest() {
  (0, _allowFromStoreFile0fkquIHc.t)(PAIRING_ALLOW_FROM_CACHE_NAMESPACE);
}
async function updateChannelAllowFromStore(params) {
  return await updateAllowFromStoreEntry({
    channel: params.channel,
    entry: params.entry,
    accountId: params.accountId,
    env: params.env,
    apply: params.apply
  });
}
async function mutateChannelAllowFromStoreEntry(params, apply) {
  return await updateChannelAllowFromStore({
    ...params,
    apply
  });
}
async function addChannelAllowFromStoreEntry(params) {
  return await mutateChannelAllowFromStoreEntry(params, (current, normalized) => {
    if (current.includes(normalized)) return null;
    return [...current, normalized];
  });
}
async function removeChannelAllowFromStoreEntry(params) {
  return await mutateChannelAllowFromStoreEntry(params, (current, normalized) => {
    const next = current.filter((entry) => entry !== normalized);
    if (next.length === current.length) return null;
    return next;
  });
}
async function listChannelPairingRequests(channel, env = process.env, accountId) {
  const filePath = resolvePairingPath(channel, env);
  return await withFileLock(filePath, {
    version: 1,
    requests: []
  }, async () => {
    const { requests: prunedExpired, removed: expiredRemoved } = await readPrunedPairingRequests(filePath);
    const { requests: pruned, removed: cappedRemoved } = pruneExcessRequestsByAccount(prunedExpired, PAIRING_PENDING_MAX);
    if (expiredRemoved || cappedRemoved) await writeJsonFile(filePath, {
      version: 1,
      requests: pruned
    });
    const normalizedAccountId = normalizePairingAccountId(accountId);
    return (normalizedAccountId ? pruned.filter((entry) => requestMatchesAccountId(entry, normalizedAccountId)) : pruned).filter((r) => r && typeof r.id === "string" && typeof r.code === "string" && typeof r.createdAt === "string").slice().toSorted((a, b) => a.createdAt.localeCompare(b.createdAt));
  });
}
async function upsertChannelPairingRequest(params) {
  const env = params.env ?? process.env;
  const filePath = resolvePairingPath(params.channel, env);
  return await withFileLock(filePath, {
    version: 1,
    requests: []
  }, async () => {
    const now = (/* @__PURE__ */new Date()).toISOString();
    const nowMs = Date.now();
    const id = normalizeId(params.id);
    const normalizedAccountId = normalizePairingAccountId(params.accountId) || "default";
    const meta = {
      ...(params.meta && typeof params.meta === "object" ? Object.fromEntries(Object.entries(params.meta).map(([k, v]) => [k, (0, _stringCoerceBje8XVt.c)(v) ?? ""]).filter(([_, v]) => Boolean(v))) : void 0),
      accountId: normalizedAccountId
    };
    let reqs = await readPairingRequests(filePath);
    const { requests: prunedExpired, removed: expiredRemoved } = pruneExpiredRequests(reqs, nowMs);
    reqs = prunedExpired;
    const normalizedMatchingAccountId = normalizedAccountId;
    const existingIdx = reqs.findIndex((r) => {
      if (r.id !== id) return false;
      return requestMatchesAccountId(r, normalizedMatchingAccountId);
    });
    const existingCodes = new Set(reqs.map((req) => ((0, _stringCoerceBje8XVt.c)(req.code) ?? "").toUpperCase()));
    if (existingIdx >= 0) {
      const existing = reqs[existingIdx];
      const code = ((0, _stringCoerceBje8XVt.c)(existing?.code) ?? "") || generateUniqueCode(existingCodes);
      const next = {
        id,
        code,
        createdAt: existing?.createdAt ?? now,
        lastSeenAt: now,
        meta: meta ?? existing?.meta
      };
      reqs[existingIdx] = next;
      const { requests: capped } = pruneExcessRequestsByAccount(reqs, PAIRING_PENDING_MAX);
      await writeJsonFile(filePath, {
        version: 1,
        requests: capped
      });
      return {
        code,
        created: false
      };
    }
    const { requests: capped, removed: cappedRemoved } = pruneExcessRequestsByAccount(reqs, PAIRING_PENDING_MAX);
    reqs = capped;
    const accountRequestCount = reqs.filter((r) => requestMatchesAccountId(r, normalizedMatchingAccountId)).length;
    if (PAIRING_PENDING_MAX > 0 && accountRequestCount >= PAIRING_PENDING_MAX) {
      if (expiredRemoved || cappedRemoved) await writeJsonFile(filePath, {
        version: 1,
        requests: reqs
      });
      return {
        code: "",
        created: false
      };
    }
    const code = generateUniqueCode(existingCodes);
    const next = {
      id,
      code,
      createdAt: now,
      lastSeenAt: now,
      ...(meta ? { meta } : {})
    };
    await writeJsonFile(filePath, {
      version: 1,
      requests: [...reqs, next]
    });
    return {
      code,
      created: true
    };
  });
}
async function approveChannelPairingCode(params) {
  const env = params.env ?? process.env;
  const code = ((0, _stringCoerceBje8XVt.o)(params.code) ?? "").toUpperCase();
  if (!code) return null;
  const filePath = resolvePairingPath(params.channel, env);
  return await withFileLock(filePath, {
    version: 1,
    requests: []
  }, async () => {
    const { requests: pruned, removed } = await readPrunedPairingRequests(filePath);
    const normalizedAccountId = normalizePairingAccountId(params.accountId);
    const idx = pruned.findIndex((r) => {
      if (r.code.toUpperCase() !== code) return false;
      return requestMatchesAccountId(r, normalizedAccountId);
    });
    if (idx < 0) {
      if (removed) await writeJsonFile(filePath, {
        version: 1,
        requests: pruned
      });
      return null;
    }
    const entry = pruned[idx];
    if (!entry) return null;
    pruned.splice(idx, 1);
    await writeJsonFile(filePath, {
      version: 1,
      requests: pruned
    });
    const entryAccountId = (0, _stringCoerceBje8XVt.c)(entry.meta?.accountId);
    await addChannelAllowFromStoreEntry({
      channel: params.channel,
      entry: entry.id,
      accountId: (0, _stringCoerceBje8XVt.c)(params.accountId) ?? entryAccountId,
      env
    });
    return {
      id: entry.id,
      entry
    };
  });
}
//#endregion /* v9-4e10bf280aaa19fe */
