"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = normalizeZaiEnv;exports.i = normalizeEnv;exports.n = isVitestRuntimeEnv;exports.r = logAcceptedEnvOption;exports.t = isTruthyEnvValue;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}
//#region src/infra/env.ts
let log = null;
let logPromise = null;
const loggedEnv = /* @__PURE__ */new Set();
async function getLog() {
  if (!log) {
    logPromise ??= Promise.resolve().then(() => jitiImport("./subsystem-DUWC_dVO.js").then((m) => _interopRequireWildcard(m))).then(({ createSubsystemLogger }) => createSubsystemLogger("env"));
    log = await logPromise;
  }
  return log;
}
function formatEnvValue(value, redact) {
  if (redact) return "<redacted>";
  const singleLine = value.replace(/\s+/g, " ").trim();
  if (singleLine.length <= 160) return singleLine;
  return `${singleLine.slice(0, 160)}…`;
}
function logAcceptedEnvOption(option) {
  if (process.env.VITEST || false) return;
  if (loggedEnv.has(option.key)) return;
  const rawValue = option.value ?? process.env[option.key];
  if (!rawValue || !rawValue.trim()) return;
  loggedEnv.add(option.key);
  getLog().then((logger) => {
    logger.info(`env: ${option.key}=${formatEnvValue(rawValue, option.redact)} (${option.description})`);
  }).catch(() => {});
}
function normalizeZaiEnv() {
  if (!process.env.ZAI_API_KEY?.trim() && process.env.Z_AI_API_KEY?.trim()) process.env.ZAI_API_KEY = process.env.Z_AI_API_KEY;
}
function isTruthyEnvValue(value) {
  if (typeof value !== "string") return false;
  switch ((0, _stringCoerceBje8XVt.a)(value)) {
    case "1":
    case "on":
    case "true":
    case "yes":return true;
    default:return false;
  }
}
function isVitestRuntimeEnv(env = process.env) {
  return env.VITEST === "true" || env.VITEST === "1" || env.VITEST_POOL_ID !== void 0 || env.VITEST_WORKER_ID !== void 0 || env.NODE_ENV === "test";
}
function normalizeEnv() {
  normalizeZaiEnv();
}
//#endregion /* v9-5b8a5ed6d3a395bf */
