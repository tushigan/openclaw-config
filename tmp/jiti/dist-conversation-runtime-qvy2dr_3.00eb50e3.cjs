"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = recordInboundSessionMetaSafe;require("./session-binding-service-7_9X79Yd.js");
require("./thread-bindings-policy-CksLUJN9.js");
require("./conversation-binding-B6iB0V05.js");
require("./binding-registry-B8HXLRqx.js");
require("./session-DJhdI8Qg.js");
require("./pairing-store-C3tDe-Lw.js");
require("./dm-policy-shared-DKaYtHuP.js");
require("./binding-targets-uoGsDs8V.js");
require("./binding-routing-CnmLSI34.js");
require("./pairing-labels-xt-XBu9p.js");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}
//#region src/channels/session-meta.ts
let inboundSessionRuntimePromise = null;
function loadInboundSessionRuntime() {
  inboundSessionRuntimePromise ??= Promise.resolve().then(() => jitiImport("./inbound.runtime-CYu9NIS8.js").then((m) => _interopRequireWildcard(m)));
  return inboundSessionRuntimePromise;
}
async function recordInboundSessionMetaSafe(params) {
  const runtime = await loadInboundSessionRuntime();
  const storePath = runtime.resolveStorePath(params.cfg.session?.store, { agentId: params.agentId });
  try {
    await runtime.recordSessionMetaFromInbound({
      storePath,
      sessionKey: params.sessionKey,
      ctx: params.ctx
    });
  } catch (err) {
    params.onError?.(err);
  }
}
//#endregion /* v9-c574abddaaf3b2a7 */
