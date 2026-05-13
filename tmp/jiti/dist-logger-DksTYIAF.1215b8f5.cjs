"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = logWarn;exports.i = logSuccess;exports.n = logError;exports.r = logInfo;exports.t = logDebug;var _themeCVJvORNs = require("./theme-CVJvORNs.js");
var _runtimeBzt9CHmD = require("./runtime-bzt9CHmD.js");
var _loggerBVNXvwCE = require("./logger-BVNXvwCE.js");
var _subsystemCxWoQXRD = require("./subsystem-CxWoQXRD.js");
//#region src/logger.ts
const subsystemPrefixRe = /^([a-z][a-z0-9-]{1,20}):\s+(.*)$/i;
function splitSubsystem(message) {
  const match = message.match(subsystemPrefixRe);
  if (!match) return null;
  const [, subsystem, rest] = match;
  return {
    subsystem,
    rest
  };
}
function logWithSubsystem(params) {
  const parsed = params.runtime === _runtimeBzt9CHmD.n ? splitSubsystem(params.message) : null;
  if (parsed) {
    (0, _subsystemCxWoQXRD.t)(parsed.subsystem)[params.subsystemMethod](parsed.rest);
    return;
  }
  params.runtime[params.runtimeMethod](params.runtimeFormatter(params.message));
  (0, _loggerBVNXvwCE.a)()[params.loggerMethod](params.message);
}
const info = _themeCVJvORNs.r.info;
const warn = _themeCVJvORNs.r.warn;
const success = _themeCVJvORNs.r.success;
const danger = _themeCVJvORNs.r.error;
function logInfo(message, runtime = _runtimeBzt9CHmD.n) {
  logWithSubsystem({
    message,
    runtime,
    runtimeMethod: "log",
    runtimeFormatter: info,
    loggerMethod: "info",
    subsystemMethod: "info"
  });
}
function logWarn(message, runtime = _runtimeBzt9CHmD.n) {
  logWithSubsystem({
    message,
    runtime,
    runtimeMethod: "log",
    runtimeFormatter: warn,
    loggerMethod: "warn",
    subsystemMethod: "warn"
  });
}
function logSuccess(message, runtime = _runtimeBzt9CHmD.n) {
  logWithSubsystem({
    message,
    runtime,
    runtimeMethod: "log",
    runtimeFormatter: success,
    loggerMethod: "info",
    subsystemMethod: "info"
  });
}
function logError(message, runtime = _runtimeBzt9CHmD.n) {
  logWithSubsystem({
    message,
    runtime,
    runtimeMethod: "error",
    runtimeFormatter: danger,
    loggerMethod: "error",
    subsystemMethod: "error"
  });
}
function logDebug(message) {
  (0, _loggerBVNXvwCE.a)().debug(message);
  if ((0, _loggerBVNXvwCE.b)()) console.log(_themeCVJvORNs.r.muted(message));
}
//#endregion /* v9-eb4afec313715378 */
