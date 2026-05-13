"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = extractDeliveryInfo;exports.c = resolveMainSessionKeyFromConfig;exports.i = serializeSessionCleanupResult;exports.n = resolveSessionCleanupAction;exports.o = readSessionHeaderStartedAtMs;exports.r = runSessionsCleanup;exports.s = resolveSessionLifecycleTimestamps;exports.t = purgeAgentSessionStoreEntries;var _sessionKeyC0K0uhmG = require("./session-key-C0K0uhmG.js");
var _agentScopeB6RIBoEj = require("./agent-scope-B6RIBoEj.js");
var _loggerBVNXvwCE = require("./logger-BVNXvwCE.js");
var _ioE69J4lLI = require("./io-E69J4lLI.js");
var _mainSessionC7L7pyed = require("./main-session-C7L7pyed.js");
var _combinedStoreGatewayD10iqlpI = require("./combined-store-gateway-D10iqlpI.js");
var _pathsDG09LEN = require("./paths-DG09LE-n.js");
var _deliveryContextSharedTofZwoN = require("./delivery-context.shared-tofZwoN5.js");
var _storeLoadDjtlQRVG = require("./store-load-DjtlQRVG.js");
var _targetsDjI6H8v = require("./targets-DjI6H-8v.js");
var _storeDvxAjGkI = require("./store-DvxAjGkI.js");
require("./reset-L5yC6_6J.js");
require("./session-key-DM4wM41_.js");
require("./session-file-MHj2gKwZ.js");
require("./transcript-Bkn4vV79.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/config/sessions/main-session.runtime.ts
function resolveMainSessionKeyFromConfig() {
  return (0, _mainSessionC7L7pyed.i)((0, _ioE69J4lLI.i)());
}
//#endregion
//#region src/config/sessions/lifecycle.ts
function resolveTimestamp(value) {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 ? value : void 0;
}
function parseTimestampMs(value) {
  if (typeof value === "number") return resolveTimestamp(value);
  if (typeof value !== "string" || !value.trim()) return;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : void 0;
}
function readFirstLine(filePath) {
  try {
    const fd = _nodeFs.default.openSync(filePath, "r");
    try {
      const buffer = Buffer.alloc(8192);
      const bytesRead = _nodeFs.default.readSync(fd, buffer, 0, buffer.length, 0);
      if (bytesRead <= 0) return;
      const chunk = buffer.subarray(0, bytesRead).toString("utf8");
      const newline = chunk.indexOf("\n");
      return newline >= 0 ? chunk.slice(0, newline) : chunk;
    } finally {
      _nodeFs.default.closeSync(fd);
    }
  } catch {
    return;
  }
}
function readSessionHeaderStartedAtMs(params) {
  const sessionId = params.entry?.sessionId?.trim();
  if (!sessionId) return;
  const pathOptions = params.pathOptions ?? (0, _pathsDG09LEN.o)({
    agentId: params.agentId,
    storePath: params.storePath
  });
  let sessionFile;
  try {
    sessionFile = (0, _pathsDG09LEN.a)(sessionId, params.entry, pathOptions);
  } catch {
    return;
  }
  const firstLine = readFirstLine(sessionFile);
  if (!firstLine) return;
  try {
    const header = JSON.parse(firstLine);
    if (header.type !== "session") return;
    if (typeof header.id === "string" && header.id.trim() && header.id !== sessionId) return;
    return parseTimestampMs(header.timestamp);
  } catch {
    return;
  }
}
function resolveSessionLifecycleTimestamps(params) {
  const entry = params.entry;
  if (!entry) return {};
  return {
    sessionStartedAt: resolveTimestamp(entry.sessionStartedAt) ?? readSessionHeaderStartedAtMs({
      entry,
      agentId: params.agentId,
      storePath: params.storePath,
      pathOptions: params.pathOptions
    }),
    lastInteractionAt: resolveTimestamp(entry.lastInteractionAt)
  };
}
//#endregion
//#region src/config/sessions/delivery-info.ts
function extractDeliveryInfo(sessionKey) {
  const hasRoutableDeliveryContext = (context) => Boolean(context?.channel && context?.to);
  const { baseSessionKey, threadId } = (0, _storeLoadDjtlQRVG.u)(sessionKey);
  if (!sessionKey || !baseSessionKey) return {
    deliveryContext: void 0,
    threadId
  };
  let deliveryContext;
  try {
    const store = (0, _storeLoadDjtlQRVG.t)((0, _pathsDG09LEN.d)((0, _ioE69J4lLI.i)().session?.store));
    let entry = store[sessionKey];
    let storedDeliveryContext = (0, _deliveryContextSharedTofZwoN.t)(entry);
    if (!hasRoutableDeliveryContext(storedDeliveryContext) && baseSessionKey !== sessionKey) {
      entry = store[baseSessionKey];
      storedDeliveryContext = (0, _deliveryContextSharedTofZwoN.t)(entry);
    }
    if (hasRoutableDeliveryContext(storedDeliveryContext)) deliveryContext = {
      channel: storedDeliveryContext.channel,
      to: storedDeliveryContext.to,
      accountId: storedDeliveryContext.accountId,
      threadId: storedDeliveryContext.threadId != null ? String(storedDeliveryContext.threadId) : void 0
    };
  } catch {}
  return {
    deliveryContext,
    threadId
  };
}
//#endregion
//#region src/config/sessions/cleanup-service.ts
function resolveSessionCleanupAction(params) {
  if (params.missingKeys.has(params.key)) return "prune-missing";
  if (params.staleKeys.has(params.key)) return "prune-stale";
  if (params.cappedKeys.has(params.key)) return "cap-overflow";
  if (params.budgetEvictedKeys.has(params.key)) return "evict-budget";
  return "keep";
}
function serializeSessionCleanupResult(params) {
  if (params.summaries.length === 1) return params.summaries[0] ?? {};
  return {
    allAgents: true,
    mode: params.mode,
    dryRun: params.dryRun,
    stores: params.summaries
  };
}
function pruneMissingTranscriptEntries(params) {
  const sessionPathOpts = (0, _pathsDG09LEN.o)({ storePath: params.storePath });
  let removed = 0;
  for (const [key, entry] of Object.entries(params.store)) {
    if (!entry?.sessionId) continue;
    const transcriptPath = (0, _pathsDG09LEN.a)(entry.sessionId, entry, sessionPathOpts);
    if (!_nodeFs.default.existsSync(transcriptPath)) {
      delete params.store[key];
      removed += 1;
      params.onPruned?.(key);
    }
  }
  return removed;
}
async function previewStoreCleanup(params) {
  const maintenance = (0, _storeLoadDjtlQRVG.r)();
  const beforeStore = (0, _storeLoadDjtlQRVG.t)(params.target.storePath, { skipCache: true });
  const previewStore = (0, _storeLoadDjtlQRVG.m)(beforeStore);
  const staleKeys = /* @__PURE__ */new Set();
  const cappedKeys = /* @__PURE__ */new Set();
  const missingKeys = /* @__PURE__ */new Set();
  const missing = params.fixMissing === true ? pruneMissingTranscriptEntries({
    store: previewStore,
    storePath: params.target.storePath,
    onPruned: (key) => {
      missingKeys.add(key);
    }
  }) : 0;
  const pruned = (0, _storeLoadDjtlQRVG.s)(previewStore, maintenance.pruneAfterMs, {
    log: false,
    onPruned: ({ key }) => {
      staleKeys.add(key);
    }
  });
  const capped = (0, _storeLoadDjtlQRVG.i)(previewStore, maintenance.maxEntries, {
    log: false,
    onCapped: ({ key }) => {
      cappedKeys.add(key);
    }
  });
  const beforeBudgetStore = (0, _storeLoadDjtlQRVG.m)(previewStore);
  const diskBudget = await (0, _storeDvxAjGkI.f)({
    store: previewStore,
    storePath: params.target.storePath,
    activeSessionKey: params.activeKey,
    maintenance,
    warnOnly: false,
    dryRun: true
  });
  const budgetEvictedKeys = /* @__PURE__ */new Set();
  for (const key of Object.keys(beforeBudgetStore)) if (!Object.hasOwn(previewStore, key)) budgetEvictedKeys.add(key);
  const beforeCount = Object.keys(beforeStore).length;
  const afterPreviewCount = Object.keys(previewStore).length;
  const wouldMutate = missing > 0 || pruned > 0 || capped > 0 || (diskBudget?.removedEntries ?? 0) > 0 || (diskBudget?.removedFiles ?? 0) > 0;
  return {
    summary: {
      agentId: params.target.agentId,
      storePath: params.target.storePath,
      mode: params.mode,
      dryRun: params.dryRun,
      beforeCount,
      afterCount: afterPreviewCount,
      missing,
      pruned,
      capped,
      diskBudget,
      wouldMutate
    },
    beforeStore,
    missingKeys,
    staleKeys,
    cappedKeys,
    budgetEvictedKeys
  };
}
async function runSessionsCleanup(params) {
  const { cfg, opts } = params;
  const mode = opts.enforce ? "enforce" : (0, _storeLoadDjtlQRVG.r)().mode;
  const targets = params.targets ?? (0, _targetsDjI6H8v.i)(cfg, {
    store: opts.store,
    agent: opts.agent,
    allAgents: opts.allAgents
  });
  const previewResults = [];
  for (const target of targets) {
    const result = await previewStoreCleanup({
      target,
      mode,
      dryRun: Boolean(opts.dryRun),
      activeKey: opts.activeKey,
      fixMissing: Boolean(opts.fixMissing)
    });
    previewResults.push(result);
  }
  const appliedSummaries = [];
  if (!opts.dryRun) for (const target of targets) {
    const appliedReportRef = { current: null };
    const missingApplied = await (0, _storeDvxAjGkI.o)(target.storePath, async (store) => {
      if (!opts.fixMissing) return 0;
      return pruneMissingTranscriptEntries({
        store,
        storePath: target.storePath
      });
    }, {
      activeSessionKey: opts.activeKey,
      maintenanceOverride: { mode },
      onMaintenanceApplied: (report) => {
        appliedReportRef.current = report;
      }
    });
    const afterStore = (0, _storeLoadDjtlQRVG.t)(target.storePath, { skipCache: true });
    const preview = previewResults.find((result) => result.summary.storePath === target.storePath);
    const appliedReport = appliedReportRef.current;
    const summary = appliedReport === null ? {
      ...(preview?.summary ?? {
        agentId: target.agentId,
        storePath: target.storePath,
        mode,
        dryRun: false,
        beforeCount: 0,
        afterCount: 0,
        missing: 0,
        pruned: 0,
        capped: 0,
        diskBudget: null,
        wouldMutate: false
      }),
      dryRun: false,
      applied: true,
      appliedCount: Object.keys(afterStore).length
    } : {
      agentId: target.agentId,
      storePath: target.storePath,
      mode: appliedReport.mode,
      dryRun: false,
      beforeCount: appliedReport.beforeCount,
      afterCount: appliedReport.afterCount,
      missing: missingApplied,
      pruned: appliedReport.pruned,
      capped: appliedReport.capped,
      diskBudget: appliedReport.diskBudget,
      wouldMutate: missingApplied > 0 || appliedReport.pruned > 0 || appliedReport.capped > 0 || (appliedReport.diskBudget?.removedEntries ?? 0) > 0 || (appliedReport.diskBudget?.removedFiles ?? 0) > 0,
      applied: true,
      appliedCount: Object.keys(afterStore).length
    };
    appliedSummaries.push(summary);
  }
  return {
    mode,
    previewResults,
    appliedSummaries
  };
}
/** Purge session store entries for a deleted agent (#65524). Best-effort. */
async function purgeAgentSessionStoreEntries(cfg, agentId) {
  try {
    const normalizedAgentId = (0, _sessionKeyC0K0uhmG.c)(agentId);
    const storeConfig = cfg.session?.store;
    const storeAgentId = typeof storeConfig === "string" && storeConfig.includes("{agentId}") ? normalizedAgentId : (0, _sessionKeyC0K0uhmG.c)((0, _agentScopeB6RIBoEj.S)(cfg));
    await (0, _storeDvxAjGkI.o)((0, _pathsDG09LEN.d)(cfg.session?.store, { agentId: normalizedAgentId }), (store) => {
      for (const key of Object.keys(store)) if ((0, _combinedStoreGatewayD10iqlpI.s)({
        cfg,
        agentId: storeAgentId,
        sessionKey: key
      }) === normalizedAgentId) delete store[key];
    });
  } catch (err) {
    (0, _loggerBVNXvwCE.a)().debug("session store purge skipped during agent delete", err);
  }
}
//#endregion /* v9-25d646e17a9fb9bb */
