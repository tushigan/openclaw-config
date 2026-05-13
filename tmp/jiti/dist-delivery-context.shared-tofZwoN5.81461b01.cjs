"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = normalizeSessionDeliveryFields;exports.i = normalizeDeliveryContext;exports.n = deliveryContextKey;exports.o = normalizeAccountId;exports.r = mergeDeliveryContext;exports.t = deliveryContextFromSession;var _accountIdBj7l9NI = require("./account-id-Bj7l9NI7.js");
var _messageChannelCoreD2XbUpib = require("./message-channel-core-D2XbUpib.js");
var _channelRouteClbSK = require("./channel-route-clbSK-46.js");
//#region src/utils/account-id.ts
function normalizeAccountId(value) {
  return (0, _accountIdBj7l9NI.r)(value);
}
//#endregion
//#region src/utils/delivery-context.shared.ts
function normalizeDeliveryContext(context) {
  if (!context) return;
  const route = (0, _channelRouteClbSK.f)({
    channel: typeof context.channel === "string" ? (0, _messageChannelCoreD2XbUpib.n)(context.channel) ?? context.channel.trim() : void 0,
    to: context.to,
    accountId: context.accountId,
    threadId: context.threadId
  });
  if (!route) return;
  const normalized = {
    channel: route.channel,
    to: (0, _channelRouteClbSK.a)(route),
    accountId: normalizeAccountId(route.accountId)
  };
  const threadId = (0, _channelRouteClbSK.c)(route);
  if (threadId != null) normalized.threadId = threadId;
  return normalized;
}
function normalizeSessionDeliveryFields(source) {
  if (!source) return {
    deliveryContext: void 0,
    lastChannel: void 0,
    lastTo: void 0,
    lastAccountId: void 0,
    lastThreadId: void 0
  };
  const merged = mergeDeliveryContext(normalizeDeliveryContext({
    channel: source.lastChannel ?? source.channel,
    to: source.lastTo,
    accountId: source.lastAccountId,
    threadId: source.lastThreadId
  }), normalizeDeliveryContext(source.deliveryContext));
  if (!merged) return {
    deliveryContext: void 0,
    lastChannel: void 0,
    lastTo: void 0,
    lastAccountId: void 0,
    lastThreadId: void 0
  };
  return {
    deliveryContext: merged,
    lastChannel: merged.channel,
    lastTo: merged.to,
    lastAccountId: merged.accountId,
    lastThreadId: merged.threadId
  };
}
function deliveryContextFromSession(entry) {
  if (!entry) return;
  return normalizeSessionDeliveryFields({
    channel: entry.channel ?? entry.origin?.provider,
    lastChannel: entry.lastChannel,
    lastTo: entry.lastTo,
    lastAccountId: entry.lastAccountId ?? entry.origin?.accountId,
    lastThreadId: entry.lastThreadId ?? entry.deliveryContext?.threadId ?? entry.origin?.threadId,
    origin: entry.origin,
    deliveryContext: entry.deliveryContext
  }).deliveryContext;
}
function mergeDeliveryContext(primary, fallback) {
  const normalizedPrimary = normalizeDeliveryContext(primary);
  const normalizedFallback = normalizeDeliveryContext(fallback);
  if (!normalizedPrimary && !normalizedFallback) return;
  const channelsConflict = normalizedPrimary?.channel && normalizedFallback?.channel && normalizedPrimary.channel !== normalizedFallback.channel;
  return normalizeDeliveryContext({
    channel: normalizedPrimary?.channel ?? normalizedFallback?.channel,
    to: channelsConflict ? normalizedPrimary?.to : normalizedPrimary?.to ?? normalizedFallback?.to,
    accountId: channelsConflict ? normalizedPrimary?.accountId : normalizedPrimary?.accountId ?? normalizedFallback?.accountId,
    threadId: channelsConflict ? normalizedPrimary?.threadId : normalizedPrimary?.threadId ?? normalizedFallback?.threadId
  });
}
function deliveryContextKey(context) {
  return (0, _channelRouteClbSK.t)(normalizeDeliveryContext(context));
}
//#endregion /* v9-ee8feec7d58ddcd9 */
