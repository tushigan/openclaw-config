"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveUndiciAutoSelectFamily;exports.r = resolveUndiciAutoSelectFamilyConnectOptions;exports.t = createUndiciAutoSelectFamilyConnectOptions;var _wslDzFVEE = require("./wsl-DzFVE-e-.js");
var net$1 = _interopRequireWildcard(require("node:net"));function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}
//#region src/infra/net/undici-family-policy.ts
const AUTO_SELECT_FAMILY_ATTEMPT_TIMEOUT_MS = 300;
function resolveUndiciAutoSelectFamily() {
  if (typeof net$1.getDefaultAutoSelectFamily !== "function") return;
  try {
    const systemDefault = net$1.getDefaultAutoSelectFamily();
    if (systemDefault && (0, _wslDzFVEE.n)()) return false;
    return systemDefault;
  } catch {
    return;
  }
}
function createUndiciAutoSelectFamilyConnectOptions(autoSelectFamily) {
  if (autoSelectFamily === void 0) return;
  return {
    autoSelectFamily,
    autoSelectFamilyAttemptTimeout: AUTO_SELECT_FAMILY_ATTEMPT_TIMEOUT_MS
  };
}
function resolveUndiciAutoSelectFamilyConnectOptions() {
  return createUndiciAutoSelectFamilyConnectOptions(resolveUndiciAutoSelectFamily());
}
//#endregion /* v9-53e2792ea2496be7 */
