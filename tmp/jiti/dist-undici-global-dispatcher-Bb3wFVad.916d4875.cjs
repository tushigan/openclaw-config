"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = forceResetGlobalDispatcher;exports.i = ensureGlobalUndiciStreamTimeouts;exports.n = void 0;exports.o = resetGlobalUndiciStreamTimeoutsForTests;exports.r = ensureGlobalUndiciEnvProxyDispatcher;exports.t = void 0;var _proxyEnvBaS80pvI = require("./proxy-env-BaS80pvI.js");
var _undiciFamilyPolicyDHD3yOap = require("./undici-family-policy-DHD3yOap.js");
var _undici = require("undici");
//#region src/infra/net/undici-global-dispatcher.ts
const DEFAULT_UNDICI_STREAM_TIMEOUT_MS = exports.t = 1800 * 1e3;
/**
* Module-level bridge so `resolveDispatcherTimeoutMs` in fetch-guard.ts
* can read the global dispatcher timeout without relying on Undici's
* non-public `.options` field.
*/
let _globalUndiciStreamTimeoutMs = exports.n = void 0;
let lastAppliedTimeoutKey = null;
let lastAppliedProxyBootstrap = false;
function resolveDispatcherKind(dispatcher) {
  const ctorName = dispatcher?.constructor?.name;
  if (typeof ctorName !== "string" || ctorName.length === 0) return "unsupported";
  if (ctorName.includes("EnvHttpProxyAgent")) return "env-proxy";
  if (ctorName.includes("ProxyAgent")) return "unsupported";
  if (ctorName.includes("Agent")) return "agent";
  return "unsupported";
}
function resolveDispatcherKey(params) {
  const autoSelectToken = params.autoSelectFamily === void 0 ? "na" : params.autoSelectFamily ? "on" : "off";
  return `${params.kind}:${params.timeoutMs}:${autoSelectToken}`;
}
function resolveCurrentDispatcherKind() {
  let dispatcher;
  try {
    dispatcher = (0, _undici.getGlobalDispatcher)();
  } catch {
    return null;
  }
  const currentKind = resolveDispatcherKind(dispatcher);
  return currentKind === "unsupported" ? null : currentKind;
}
function ensureGlobalUndiciEnvProxyDispatcher() {
  if (!(0, _proxyEnvBaS80pvI.n)()) return;
  if (lastAppliedProxyBootstrap) {
    if (resolveCurrentDispatcherKind() === "env-proxy") return;
    lastAppliedProxyBootstrap = false;
  }
  const currentKind = resolveCurrentDispatcherKind();
  if (currentKind === null) return;
  if (currentKind === "env-proxy") {
    lastAppliedProxyBootstrap = true;
    return;
  }
  try {
    (0, _undici.setGlobalDispatcher)(new _undici.EnvHttpProxyAgent((0, _proxyEnvBaS80pvI.o)()));
    lastAppliedProxyBootstrap = true;
  } catch {}
}
function ensureGlobalUndiciStreamTimeouts(opts) {
  const timeoutMsRaw = opts?.timeoutMs ?? 18e5;
  if (!Number.isFinite(timeoutMsRaw)) return;
  const timeoutMs = Math.max(DEFAULT_UNDICI_STREAM_TIMEOUT_MS, Math.floor(timeoutMsRaw));
  exports.n = _globalUndiciStreamTimeoutMs = timeoutMs;
  const kind = resolveCurrentDispatcherKind();
  if (kind === null) return;
  const autoSelectFamily = (0, _undiciFamilyPolicyDHD3yOap.n)();
  const nextKey = resolveDispatcherKey({
    kind,
    timeoutMs,
    autoSelectFamily
  });
  if (lastAppliedTimeoutKey === nextKey) return;
  const connect = (0, _undiciFamilyPolicyDHD3yOap.t)(autoSelectFamily);
  try {
    if (kind === "env-proxy") (0, _undici.setGlobalDispatcher)(new _undici.EnvHttpProxyAgent({
      ...(0, _proxyEnvBaS80pvI.o)(),
      bodyTimeout: timeoutMs,
      headersTimeout: timeoutMs,
      ...(connect ? { connect } : {})
    }));else
    (0, _undici.setGlobalDispatcher)(new _undici.Agent({
      bodyTimeout: timeoutMs,
      headersTimeout: timeoutMs,
      ...(connect ? { connect } : {})
    }));
    lastAppliedTimeoutKey = nextKey;
  } catch {}
}
function resetGlobalUndiciStreamTimeoutsForTests() {
  lastAppliedTimeoutKey = null;
  lastAppliedProxyBootstrap = false;
  exports.n = _globalUndiciStreamTimeoutMs = void 0;
}
/**
* Re-evaluate proxy env changes for undici. Installs EnvHttpProxyAgent when
* proxy env is present, and restores a direct Agent after proxy env is cleared.
*/
function forceResetGlobalDispatcher() {
  lastAppliedTimeoutKey = null;
  lastAppliedProxyBootstrap = false;
  try {
    const proxyOptions = (0, _proxyEnvBaS80pvI.o)();
    if ((0, _proxyEnvBaS80pvI.n)()) {
      (0, _undici.setGlobalDispatcher)(new _undici.EnvHttpProxyAgent(proxyOptions));
      lastAppliedProxyBootstrap = true;
    } else (0, _undici.setGlobalDispatcher)(new _undici.Agent());
  } catch {}
}
//#endregion /* v9-c25a77fcd35cee6e */
