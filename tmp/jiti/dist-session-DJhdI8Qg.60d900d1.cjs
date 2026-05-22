"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = recordInboundSession;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}
//#region src/channels/session.ts
let inboundSessionRuntimePromise = null;
function loadInboundSessionRuntime() {
  inboundSessionRuntimePromise ??= Promise.resolve().then(() => jitiImport("./inbound.runtime-CYu9NIS8.js").then((m) => _interopRequireWildcard(m)));
  return inboundSessionRuntimePromise;
}
function shouldSkipPinnedMainDmRouteUpdate(pin) {
  if (!pin) return false;
  const owner = (0, _stringCoerceBje8XVt.a)(pin.ownerRecipient);
  const sender = (0, _stringCoerceBje8XVt.a)(pin.senderRecipient);
  if (!owner || !sender || owner === sender) return false;
  pin.onSkip?.({
    ownerRecipient: pin.ownerRecipient,
    senderRecipient: pin.senderRecipient
  });
  return true;
}
async function recordInboundSession(params) {
  const { storePath, sessionKey, ctx, groupResolution, createIfMissing } = params;
  const canonicalSessionKey = (0, _stringCoerceBje8XVt.a)(sessionKey);
  const runtime = await loadInboundSessionRuntime();
  const metaTask = runtime.recordSessionMetaFromInbound({
    storePath,
    sessionKey: canonicalSessionKey,
    ctx,
    groupResolution,
    createIfMissing
  }).catch(params.onRecordError);
  params.trackSessionMetaTask?.(metaTask);
  const update = params.updateLastRoute;
  if (!update) return;
  if (shouldSkipPinnedMainDmRouteUpdate(update.mainDmOwnerPin)) return;
  const targetSessionKey = (0, _stringCoerceBje8XVt.a)(update.sessionKey);
  await runtime.updateLastRoute({
    storePath,
    sessionKey: targetSessionKey,
    deliveryContext: {
      channel: update.channel,
      to: update.to,
      accountId: update.accountId,
      threadId: update.threadId
    },
    ctx: targetSessionKey === canonicalSessionKey ? ctx : void 0,
    groupResolution,
    createIfMissing
  });
}
//#endregion /* v9-903bb84d60cc9f7e */
