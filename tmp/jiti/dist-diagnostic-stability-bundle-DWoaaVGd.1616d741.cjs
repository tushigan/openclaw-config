"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = installDiagnosticStabilityFatalHook;exports.c = readLatestDiagnosticStabilityBundleSync;exports.d = uninstallDiagnosticStabilityFatalHook;exports.f = writeDiagnosticStabilityBundleForFailureSync;exports.i = void 0;exports.l = resetDiagnosticStabilityBundleForTest;exports.n = void 0;exports.o = listDiagnosticStabilityBundleFilesSync;exports.p = writeDiagnosticStabilityBundleSync;exports.r = void 0;exports.s = readDiagnosticStabilityBundleFileSync;exports.t = void 0;exports.u = resolveDiagnosticStabilityBundleDir;var _redact1fZUZMlV = require("./redact-1fZUZMlV.js");
var _pathsC1_Y0cDn = require("./paths-C1_Y0cDn.js");
var _fatalErrorHooks4xzPL8p = require("./fatal-error-hooks-4xzPL8p8.js");
var _diagnosticStabilityBzDrfjbc = require("./diagnostic-stability-BzDrfjbc.js");
var _nodeProcess = _interopRequireDefault(require("node:process"));
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/logging/diagnostic-stability-bundle.ts
const DIAGNOSTIC_STABILITY_BUNDLE_VERSION = exports.r = 1;
const DEFAULT_DIAGNOSTIC_STABILITY_BUNDLE_LIMIT = exports.t = _diagnosticStabilityBzDrfjbc.t;
const DEFAULT_DIAGNOSTIC_STABILITY_BUNDLE_RETENTION = exports.n = 20;
const MAX_DIAGNOSTIC_STABILITY_BUNDLE_BYTES = exports.i = 5 * 1024 * 1024;
const SAFE_REASON_CODE = /^[A-Za-z0-9_.:-]{1,120}$/u;
const BUNDLE_PREFIX = "openclaw-stability-";
const BUNDLE_SUFFIX = ".json";
const REDACTED_HOSTNAME = "<redacted-hostname>";
const MAX_SAFE_ERROR_MESSAGE_LENGTH = 500;
let fatalHookUnsubscribe = null;
function normalizeReason(reason) {
  return SAFE_REASON_CODE.test(reason) ? reason : "unknown";
}
function formatBundleTimestamp(now) {
  return now.toISOString().replace(/[:.]/g, "-");
}
function readErrorCode(error) {
  if (!error || typeof error !== "object" || !("code" in error)) return;
  const code = error.code;
  if (typeof code === "string" && SAFE_REASON_CODE.test(code)) return code;
  if (typeof code === "number" && Number.isFinite(code)) return String(code);
}
function readErrorName(error) {
  if (!error || typeof error !== "object" || !("name" in error)) return;
  const name = error.name;
  return typeof name === "string" && SAFE_REASON_CODE.test(name) ? name : void 0;
}
function readErrorMessage(error) {
  if (!error || typeof error !== "object" || !("message" in error)) return;
  const message = error.message;
  if (typeof message !== "string") return;
  const sanitized = (0, _redact1fZUZMlV.i)(message, { mode: "tools" }).replace(/\s+/gu, " ").trim();
  if (!sanitized) return;
  return sanitized.length > MAX_SAFE_ERROR_MESSAGE_LENGTH ? `${sanitized.slice(0, MAX_SAFE_ERROR_MESSAGE_LENGTH)}...` : sanitized;
}
function readSafeErrorMetadata(error) {
  const name = readErrorName(error);
  const code = readErrorCode(error);
  const message = readErrorMessage(error);
  if (!name && !code && !message) return;
  return {
    ...(name ? { name } : {}),
    ...(code ? { code } : {}),
    ...(message ? { message } : {})
  };
}
function resolveDiagnosticStabilityBundleDir(options = {}) {
  return _nodePath.default.join(options.stateDir ?? (0, _pathsC1_Y0cDn.v)(options.env ?? _nodeProcess.default.env), "logs", "stability");
}
function buildBundlePath(dir, now, reason) {
  return _nodePath.default.join(dir, `${BUNDLE_PREFIX}${formatBundleTimestamp(now)}-${_nodeProcess.default.pid}-${normalizeReason(reason)}${BUNDLE_SUFFIX}`);
}
function isBundleFile(name) {
  return name.startsWith(BUNDLE_PREFIX) && name.endsWith(BUNDLE_SUFFIX);
}
function isMissingFileError(error) {
  return typeof error === "object" && error !== null && "code" in error && error.code === "ENOENT";
}
function readObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(`Invalid stability bundle: ${label} must be an object`);
  return value;
}
function readNumber(value, label) {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`Invalid stability bundle: ${label} must be a finite number`);
  return value;
}
function readTimestampMs(value, label) {
  const timestamp = readNumber(value, label);
  if (Number.isNaN(new Date(timestamp).getTime())) throw new Error(`Invalid stability bundle: ${label} must be a valid timestamp`);
  return timestamp;
}
function readOptionalNumber(value, label) {
  if (value === void 0) return;
  return readNumber(value, label);
}
function readString(value, label) {
  if (typeof value !== "string") throw new Error(`Invalid stability bundle: ${label} must be a string`);
  return value;
}
function readTimestampString(value, label) {
  const timestamp = readString(value, label);
  if (Number.isNaN(new Date(timestamp).getTime())) throw new Error(`Invalid stability bundle: ${label} must be a valid timestamp`);
  return timestamp;
}
function readCodeString(value, label) {
  const code = readString(value, label);
  if (!SAFE_REASON_CODE.test(code)) throw new Error(`Invalid stability bundle: ${label} must be a safe diagnostic code`);
  return code;
}
function readOptionalCodeString(value, label) {
  if (value === void 0) return;
  const code = readString(value, label);
  return SAFE_REASON_CODE.test(code) ? code : void 0;
}
function assignOptionalNumber(target, key, value, label) {
  const parsed = readOptionalNumber(value, label);
  if (parsed !== void 0) target[key] = parsed;
}
function assignOptionalCodeString(target, key, value, label) {
  const parsed = readOptionalCodeString(value, label);
  if (parsed !== void 0) target[key] = parsed;
}
function readMemoryUsage(value, label) {
  const memory = readObject(value, label);
  return {
    rssBytes: readNumber(memory.rssBytes, `${label}.rssBytes`),
    heapTotalBytes: readNumber(memory.heapTotalBytes, `${label}.heapTotalBytes`),
    heapUsedBytes: readNumber(memory.heapUsedBytes, `${label}.heapUsedBytes`),
    externalBytes: readNumber(memory.externalBytes, `${label}.externalBytes`),
    arrayBuffersBytes: readNumber(memory.arrayBuffersBytes, `${label}.arrayBuffersBytes`)
  };
}
function readNumberMap(value, label) {
  const source = readObject(value, label);
  const result = {};
  for (const [key, entry] of Object.entries(source)) {
    if (!SAFE_REASON_CODE.test(key)) continue;
    result[key] = readNumber(entry, `${label}.${key}`);
  }
  return result;
}
function readOptionalMemorySummary(value) {
  if (value === void 0) return;
  const memory = readObject(value, "snapshot.summary.memory");
  const latest = memory.latest === void 0 ? void 0 : readMemoryUsage(memory.latest, "snapshot.summary.memory.latest");
  return {
    ...(latest ? { latest } : {}),
    ...(memory.maxRssBytes !== void 0 ? { maxRssBytes: readNumber(memory.maxRssBytes, "snapshot.summary.memory.maxRssBytes") } : {}),
    ...(memory.maxHeapUsedBytes !== void 0 ? { maxHeapUsedBytes: readNumber(memory.maxHeapUsedBytes, "snapshot.summary.memory.maxHeapUsedBytes") } : {}),
    pressureCount: readNumber(memory.pressureCount, "snapshot.summary.memory.pressureCount")
  };
}
function readOptionalPayloadLargeSummary(value) {
  if (value === void 0) return;
  const payloadLarge = readObject(value, "snapshot.summary.payloadLarge");
  return {
    count: readNumber(payloadLarge.count, "snapshot.summary.payloadLarge.count"),
    rejected: readNumber(payloadLarge.rejected, "snapshot.summary.payloadLarge.rejected"),
    truncated: readNumber(payloadLarge.truncated, "snapshot.summary.payloadLarge.truncated"),
    chunked: readNumber(payloadLarge.chunked, "snapshot.summary.payloadLarge.chunked"),
    bySurface: readNumberMap(payloadLarge.bySurface, "snapshot.summary.payloadLarge.bySurface")
  };
}
function readStabilityEventRecord(value, label) {
  const record = readObject(value, label);
  const sanitized = {
    seq: readNumber(record.seq, `${label}.seq`),
    ts: readTimestampMs(record.ts, `${label}.ts`),
    type: readCodeString(record.type, `${label}.type`)
  };
  assignOptionalCodeString(sanitized, "channel", record.channel, `${label}.channel`);
  assignOptionalCodeString(sanitized, "pluginId", record.pluginId, `${label}.pluginId`);
  assignOptionalCodeString(sanitized, "source", record.source, `${label}.source`);
  assignOptionalCodeString(sanitized, "surface", record.surface, `${label}.surface`);
  assignOptionalCodeString(sanitized, "action", record.action, `${label}.action`);
  assignOptionalCodeString(sanitized, "reason", record.reason, `${label}.reason`);
  assignOptionalCodeString(sanitized, "outcome", record.outcome, `${label}.outcome`);
  assignOptionalCodeString(sanitized, "level", record.level, `${label}.level`);
  assignOptionalCodeString(sanitized, "phase", record.phase, `${label}.phase`);
  assignOptionalCodeString(sanitized, "detector", record.detector, `${label}.detector`);
  assignOptionalCodeString(sanitized, "toolName", record.toolName, `${label}.toolName`);
  assignOptionalCodeString(sanitized, "activeWorkKind", record.activeWorkKind, `${label}.activeWorkKind`);
  assignOptionalCodeString(sanitized, "pairedToolName", record.pairedToolName, `${label}.pairedToolName`);
  assignOptionalCodeString(sanitized, "provider", record.provider, `${label}.provider`);
  assignOptionalCodeString(sanitized, "model", record.model, `${label}.model`);
  assignOptionalNumber(sanitized, "durationMs", record.durationMs, `${label}.durationMs`);
  assignOptionalNumber(sanitized, "requestBytes", record.requestBytes, `${label}.requestBytes`);
  assignOptionalNumber(sanitized, "responseBytes", record.responseBytes, `${label}.responseBytes`);
  assignOptionalNumber(sanitized, "timeToFirstByteMs", record.timeToFirstByteMs, `${label}.timeToFirstByteMs`);
  assignOptionalNumber(sanitized, "costUsd", record.costUsd, `${label}.costUsd`);
  assignOptionalNumber(sanitized, "count", record.count, `${label}.count`);
  assignOptionalNumber(sanitized, "bytes", record.bytes, `${label}.bytes`);
  assignOptionalNumber(sanitized, "limitBytes", record.limitBytes, `${label}.limitBytes`);
  assignOptionalNumber(sanitized, "thresholdBytes", record.thresholdBytes, `${label}.thresholdBytes`);
  assignOptionalNumber(sanitized, "rssGrowthBytes", record.rssGrowthBytes, `${label}.rssGrowthBytes`);
  assignOptionalNumber(sanitized, "windowMs", record.windowMs, `${label}.windowMs`);
  assignOptionalNumber(sanitized, "ageMs", record.ageMs, `${label}.ageMs`);
  assignOptionalNumber(sanitized, "queueDepth", record.queueDepth, `${label}.queueDepth`);
  assignOptionalNumber(sanitized, "queueSize", record.queueSize, `${label}.queueSize`);
  assignOptionalNumber(sanitized, "waitMs", record.waitMs, `${label}.waitMs`);
  assignOptionalNumber(sanitized, "active", record.active, `${label}.active`);
  assignOptionalNumber(sanitized, "waiting", record.waiting, `${label}.waiting`);
  assignOptionalNumber(sanitized, "queued", record.queued, `${label}.queued`);
  if (record.webhooks !== void 0) {
    const webhooks = readObject(record.webhooks, `${label}.webhooks`);
    sanitized.webhooks = {
      received: readNumber(webhooks.received, `${label}.webhooks.received`),
      processed: readNumber(webhooks.processed, `${label}.webhooks.processed`),
      errors: readNumber(webhooks.errors, `${label}.webhooks.errors`)
    };
  }
  if (record.memory !== void 0) sanitized.memory = readMemoryUsage(record.memory, `${label}.memory`);
  if (record.usage !== void 0) {
    const usage = readObject(record.usage, `${label}.usage`);
    sanitized.usage = {
      ...(usage.input !== void 0 ? { input: readNumber(usage.input, `${label}.usage.input`) } : {}),
      ...(usage.output !== void 0 ? { output: readNumber(usage.output, `${label}.usage.output`) } : {}),
      ...(usage.cacheRead !== void 0 ? { cacheRead: readNumber(usage.cacheRead, `${label}.usage.cacheRead`) } : {}),
      ...(usage.cacheWrite !== void 0 ? { cacheWrite: readNumber(usage.cacheWrite, `${label}.usage.cacheWrite`) } : {}),
      ...(usage.promptTokens !== void 0 ? { promptTokens: readNumber(usage.promptTokens, `${label}.usage.promptTokens`) } : {}),
      ...(usage.total !== void 0 ? { total: readNumber(usage.total, `${label}.usage.total`) } : {})
    };
  }
  if (record.context !== void 0) {
    const context = readObject(record.context, `${label}.context`);
    sanitized.context = {
      ...(context.limit !== void 0 ? { limit: readNumber(context.limit, `${label}.context.limit`) } : {}),
      ...(context.used !== void 0 ? { used: readNumber(context.used, `${label}.context.used`) } : {})
    };
  }
  return sanitized;
}
function readStabilitySnapshot(value) {
  const snapshot = readObject(value, "snapshot");
  const generatedAt = readTimestampString(snapshot.generatedAt, "snapshot.generatedAt");
  const capacity = readNumber(snapshot.capacity, "snapshot.capacity");
  const count = readNumber(snapshot.count, "snapshot.count");
  const dropped = readNumber(snapshot.dropped, "snapshot.dropped");
  const firstSeq = readOptionalNumber(snapshot.firstSeq, "snapshot.firstSeq");
  const lastSeq = readOptionalNumber(snapshot.lastSeq, "snapshot.lastSeq");
  if (!Array.isArray(snapshot.events)) throw new Error("Invalid stability bundle: snapshot.events must be an array");
  const events = snapshot.events.map((event, index) => readStabilityEventRecord(event, `snapshot.events[${index}]`));
  const summary = readObject(snapshot.summary, "snapshot.summary");
  return {
    generatedAt,
    capacity,
    count,
    dropped,
    ...(firstSeq !== void 0 ? { firstSeq } : {}),
    ...(lastSeq !== void 0 ? { lastSeq } : {}),
    events,
    summary: {
      byType: readNumberMap(summary.byType, "snapshot.summary.byType"),
      ...(summary.memory !== void 0 ? { memory: readOptionalMemorySummary(summary.memory) } : {}),
      ...(summary.payloadLarge !== void 0 ? { payloadLarge: readOptionalPayloadLargeSummary(summary.payloadLarge) } : {})
    }
  };
}
function parseDiagnosticStabilityBundle(value) {
  const bundle = readObject(value, "bundle");
  if (bundle.version !== 1) throw new Error(`Unsupported stability bundle version: ${String(bundle.version)}`);
  const processInfo = readObject(bundle.process, "process");
  readObject(bundle.host, "host");
  const error = bundle.error === void 0 ? void 0 : readSafeErrorMetadata(bundle.error);
  return {
    version: 1,
    generatedAt: readTimestampString(bundle.generatedAt, "generatedAt"),
    reason: normalizeReason(readString(bundle.reason, "reason")),
    process: {
      pid: readNumber(processInfo.pid, "process.pid"),
      platform: readCodeString(processInfo.platform, "process.platform"),
      arch: readCodeString(processInfo.arch, "process.arch"),
      node: readCodeString(processInfo.node, "process.node"),
      uptimeMs: readNumber(processInfo.uptimeMs, "process.uptimeMs")
    },
    host: { hostname: REDACTED_HOSTNAME },
    ...(error ? { error } : {}),
    snapshot: readStabilitySnapshot(bundle.snapshot)
  };
}
function listDiagnosticStabilityBundleFilesSync(options = {}) {
  const dir = resolveDiagnosticStabilityBundleDir(options);
  try {
    return _nodeFs.default.readdirSync(dir, { withFileTypes: true }).filter((entry) => entry.isFile() && isBundleFile(entry.name)).map((entry) => {
      const file = _nodePath.default.join(dir, entry.name);
      return {
        path: file,
        mtimeMs: _nodeFs.default.statSync(file).mtimeMs
      };
    }).toSorted((a, b) => b.mtimeMs - a.mtimeMs || b.path.localeCompare(a.path));
  } catch (error) {
    if (isMissingFileError(error)) return [];
    throw error;
  }
}
function readDiagnosticStabilityBundleFileSync(file) {
  try {
    const stat = _nodeFs.default.statSync(file);
    if (stat.size > 5242880) throw new Error(`Stability bundle is too large: ${stat.size} bytes exceeds ${MAX_DIAGNOSTIC_STABILITY_BUNDLE_BYTES}`);
    const raw = _nodeFs.default.readFileSync(file, "utf8");
    const bundle = parseDiagnosticStabilityBundle(JSON.parse(raw));
    return {
      status: "found",
      path: file,
      mtimeMs: stat.mtimeMs,
      bundle
    };
  } catch (error) {
    return {
      status: "failed",
      path: file,
      error
    };
  }
}
function readLatestDiagnosticStabilityBundleSync(options = {}) {
  try {
    const latest = listDiagnosticStabilityBundleFilesSync(options)[0];
    if (!latest) return {
      status: "missing",
      dir: resolveDiagnosticStabilityBundleDir(options)
    };
    return readDiagnosticStabilityBundleFileSync(latest.path);
  } catch (error) {
    return {
      status: "failed",
      error
    };
  }
}
function pruneOldBundles(dir, retention) {
  if (!Number.isFinite(retention) || retention < 1) return;
  try {
    const entries = _nodeFs.default.readdirSync(dir, { withFileTypes: true }).filter((entry) => entry.isFile() && isBundleFile(entry.name)).map((entry) => {
      const file = _nodePath.default.join(dir, entry.name);
      let mtimeMs = 0;
      try {
        mtimeMs = _nodeFs.default.statSync(file).mtimeMs;
      } catch {}
      return {
        file,
        mtimeMs
      };
    }).toSorted((a, b) => b.mtimeMs - a.mtimeMs || b.file.localeCompare(a.file));
    for (const entry of entries.slice(retention)) try {
      _nodeFs.default.unlinkSync(entry.file);
    } catch {}
  } catch {}
}
function writeDiagnosticStabilityBundleSync(options) {
  try {
    const now = options.now ?? /* @__PURE__ */new Date();
    const snapshot = (0, _diagnosticStabilityBzDrfjbc.n)({ limit: options.limit ?? DEFAULT_DIAGNOSTIC_STABILITY_BUNDLE_LIMIT });
    if (!options.includeEmpty && snapshot.count === 0) return {
      status: "skipped",
      reason: "empty"
    };
    const reason = normalizeReason(options.reason);
    const error = options.error ? readSafeErrorMetadata(options.error) : void 0;
    const bundle = {
      version: 1,
      generatedAt: now.toISOString(),
      reason,
      process: {
        pid: _nodeProcess.default.pid,
        platform: _nodeProcess.default.platform,
        arch: _nodeProcess.default.arch,
        node: _nodeProcess.default.versions.node,
        uptimeMs: Math.round(_nodeProcess.default.uptime() * 1e3)
      },
      host: { hostname: REDACTED_HOSTNAME },
      ...(error ? { error } : {}),
      snapshot
    };
    const dir = resolveDiagnosticStabilityBundleDir(options);
    _nodeFs.default.mkdirSync(dir, {
      recursive: true,
      mode: 448
    });
    const file = buildBundlePath(dir, now, reason);
    const tmpFile = `${file}.${_nodeProcess.default.pid}.tmp`;
    _nodeFs.default.writeFileSync(tmpFile, `${JSON.stringify(bundle, null, 2)}\n`, {
      encoding: "utf8",
      mode: 384
    });
    _nodeFs.default.renameSync(tmpFile, file);
    pruneOldBundles(dir, options.retention ?? 20);
    return {
      status: "written",
      path: file,
      bundle
    };
  } catch (error) {
    return {
      status: "failed",
      error
    };
  }
}
function writeDiagnosticStabilityBundleForFailureSync(reason, error, options = {}) {
  const result = writeDiagnosticStabilityBundleSync({
    ...options,
    reason,
    error,
    includeEmpty: true
  });
  if (result.status === "written") return {
    status: "written",
    path: result.path,
    message: `wrote stability bundle: ${result.path}`
  };
  if (result.status === "failed") return {
    status: "failed",
    error: result.error,
    message: `failed to write stability bundle: ${String(result.error)}`
  };
  return result;
}
function installDiagnosticStabilityFatalHook(options = {}) {
  if (fatalHookUnsubscribe) return;
  fatalHookUnsubscribe = (0, _fatalErrorHooks4xzPL8p.t)(({ reason, error }) => {
    const result = writeDiagnosticStabilityBundleForFailureSync(reason, error, options);
    return "message" in result ? result.message : void 0;
  });
}
function uninstallDiagnosticStabilityFatalHook() {
  fatalHookUnsubscribe?.();
  fatalHookUnsubscribe = null;
}
function resetDiagnosticStabilityBundleForTest() {
  uninstallDiagnosticStabilityFatalHook();
}
//#endregion /* v9-3d73e212aa88b240 */
