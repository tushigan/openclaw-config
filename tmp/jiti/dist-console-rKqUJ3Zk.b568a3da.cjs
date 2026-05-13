"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = routeLogsToStderr;exports.c = setConsoleTimestampPrefix;exports.i = getResolvedConsoleSettings;exports.l = shouldLogSubsystemToConsole;exports.n = formatConsoleTimestamp;exports.o = setConsoleConfigLoaderForTests;exports.r = getConsoleSettings;exports.s = setConsoleSubsystemFilter;exports.t = enableConsoleCapture;var _redact1fZUZMlV = require("./redact-1fZUZMlV.js");
var _ansiDqm1lzVL = require("./ansi-Dqm1lzVL.js");
var _loggerBVNXvwCE = require("./logger-BVNXvwCE.js");
var _nodeUtil = _interopRequireDefault(require("node:util"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/logging/console.ts
const loadConfigFallbackDefault = () => void 0;
let loadConfigFallback = loadConfigFallbackDefault;
function setConsoleConfigLoaderForTests(loader) {
  loadConfigFallback = loader ?? loadConfigFallbackDefault;
}
function normalizeConsoleLevel(level) {
  if ((0, _loggerBVNXvwCE.b)()) return "debug";
  if (!level && process.env.VITEST === "true" && process.env.OPENCLAW_TEST_CONSOLE !== "1") return "silent";
  return (0, _loggerBVNXvwCE.v)(level, "info");
}
function normalizeConsoleStyle(style) {
  if (style === "compact" || style === "json" || style === "pretty") return style;
  if (!process.stdout.isTTY) return "compact";
  return "pretty";
}
function resolveConsoleSettings() {
  const envLevel = (0, _loggerBVNXvwCE.m)();
  if (process.env.VITEST === "true" && process.env.OPENCLAW_TEST_CONSOLE !== "1" && !(0, _loggerBVNXvwCE.b)() && !envLevel && !_loggerBVNXvwCE.h.overrideSettings) return {
    level: "silent",
    style: normalizeConsoleStyle(void 0)
  };
  let cfg = _loggerBVNXvwCE.h.overrideSettings ?? (0, _redact1fZUZMlV.c)();
  if (!cfg && !(0, _redact1fZUZMlV.l)()) if (_loggerBVNXvwCE.h.resolvingConsoleSettings) cfg = void 0;else
  {
    _loggerBVNXvwCE.h.resolvingConsoleSettings = true;
    try {
      cfg = loadConfigFallback();
    } finally {
      _loggerBVNXvwCE.h.resolvingConsoleSettings = false;
    }
  }
  return {
    level: envLevel ?? normalizeConsoleLevel(cfg?.consoleLevel),
    style: normalizeConsoleStyle(cfg?.consoleStyle)
  };
}
function consoleSettingsChanged(a, b) {
  if (!a) return true;
  return a.level !== b.level || a.style !== b.style;
}
function getConsoleSettings() {
  const settings = resolveConsoleSettings();
  const cached = _loggerBVNXvwCE.h.cachedConsoleSettings;
  if (!cached || consoleSettingsChanged(cached, settings)) _loggerBVNXvwCE.h.cachedConsoleSettings = settings;
  return _loggerBVNXvwCE.h.cachedConsoleSettings;
}
function getResolvedConsoleSettings() {
  return getConsoleSettings();
}
function routeLogsToStderr() {
  _loggerBVNXvwCE.h.forceConsoleToStderr = true;
}
function setConsoleSubsystemFilter(filters) {
  if (!filters || filters.length === 0) {
    _loggerBVNXvwCE.h.consoleSubsystemFilter = null;
    return;
  }
  const normalized = filters.map((value) => value.trim()).filter((value) => value.length > 0);
  _loggerBVNXvwCE.h.consoleSubsystemFilter = normalized.length > 0 ? normalized : null;
}
function setConsoleTimestampPrefix(enabled) {
  _loggerBVNXvwCE.h.consoleTimestampPrefix = enabled;
}
function normalizeConsoleSubsystem(subsystem) {
  if (typeof subsystem !== "string") return null;
  const normalized = subsystem.trim();
  return normalized.length > 0 ? normalized : null;
}
function shouldLogSubsystemToConsole(subsystem) {
  const filter = _loggerBVNXvwCE.h.consoleSubsystemFilter;
  if (!filter || filter.length === 0) return true;
  const normalizedSubsystem = normalizeConsoleSubsystem(subsystem);
  if (!normalizedSubsystem) return false;
  return filter.some((prefix) => normalizedSubsystem === prefix || normalizedSubsystem.startsWith(`${prefix}/`));
}
const SUPPRESSED_CONSOLE_PREFIXES = [
"Closing session:",
"Opening session:",
"Removing old closed session:",
"Session already closed",
"Session already open"];

function shouldSuppressConsoleMessage(message) {
  if ((0, _loggerBVNXvwCE.b)()) return false;
  if (SUPPRESSED_CONSOLE_PREFIXES.some((prefix) => message.startsWith(prefix))) return true;
  return false;
}
function isEpipeError(err) {
  const code = err?.code;
  return code === "EPIPE" || code === "EIO";
}
function formatConsoleTimestamp(style) {
  const now = /* @__PURE__ */new Date();
  if (style === "pretty") return (0, _loggerBVNXvwCE.f)(now, { style: "short" }).replace(/[+-]\d{2}:\d{2}$/, "");
  return (0, _loggerBVNXvwCE.d)(now);
}
function hasTimestampPrefix(value) {
  return /^(?:\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)/.test(value);
}
/**
* Route console.* calls through file logging while still emitting to stdout/stderr.
* This keeps user-facing output unchanged but guarantees every console call is captured in log files.
*/
function enableConsoleCapture() {
  if (_loggerBVNXvwCE.h.consolePatched) return;
  _loggerBVNXvwCE.h.consolePatched = true;
  if (!_loggerBVNXvwCE.h.streamErrorHandlersInstalled) {
    _loggerBVNXvwCE.h.streamErrorHandlersInstalled = true;
    for (const stream of [process.stdout, process.stderr]) stream.on("error", (err) => {
      if (isEpipeError(err)) return;
      throw err;
    });
  }
  let logger = null;
  const getLoggerLazy = () => {
    if (!logger) logger = (0, _loggerBVNXvwCE.a)();
    return logger;
  };
  const original = {
    log: console.log,
    info: console.info,
    warn: console.warn,
    error: console.error,
    debug: console.debug,
    trace: console.trace
  };
  _loggerBVNXvwCE.h.rawConsole = {
    log: original.log,
    info: original.info,
    warn: original.warn,
    error: original.error
  };
  const forward = (level, orig) => (...args) => {
    const formatted = _nodeUtil.default.format(...args);
    if (shouldSuppressConsoleMessage(formatted)) return;
    const trimmed = (0, _ansiDqm1lzVL.r)(formatted).trimStart();
    const timestamp = _loggerBVNXvwCE.h.consoleTimestampPrefix && trimmed.length > 0 && !hasTimestampPrefix(trimmed) ? formatConsoleTimestamp(getConsoleSettings().style) : "";
    try {
      const resolvedLogger = getLoggerLazy();
      if (level === "trace") resolvedLogger.trace(formatted);else
      if (level === "debug") resolvedLogger.debug(formatted);else
      if (level === "info") resolvedLogger.info(formatted);else
      if (level === "warn") resolvedLogger.warn(formatted);else
      if (level === "error" || level === "fatal") resolvedLogger.error(formatted);else
      resolvedLogger.info(formatted);
    } catch {}
    if (_loggerBVNXvwCE.h.forceConsoleToStderr) try {
      const redacted = (0, _redact1fZUZMlV.i)(formatted);
      const line = timestamp ? `${timestamp} ${redacted}` : redacted;
      process.stderr.write(`${line}\n`);
    } catch (err) {
      if (isEpipeError(err)) return;
      throw err;
    } else
    try {
      const redacted = (0, _redact1fZUZMlV.i)(formatted);
      if (!timestamp) {
        if (args.length === 0) {
          orig.apply(console, args);
          return;
        }
        orig.call(console, redacted);
        return;
      }
      orig.call(console, redacted ? `${timestamp} ${redacted}` : timestamp);
    } catch (err) {
      if (isEpipeError(err)) return;
      throw err;
    }
  };
  console.log = forward("info", original.log);
  console.info = forward("info", original.info);
  console.warn = forward("warn", original.warn);
  console.error = forward("error", original.error);
  console.debug = forward("debug", original.debug);
  console.trace = forward("trace", original.trace);
}
//#endregion /* v9-d282ef5f75aa2dc0 */
