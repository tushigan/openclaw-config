"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = channelRouteTarget;exports.c = channelRouteThreadId;exports.d = normalizeChannelRouteRef;exports.f = normalizeChannelRouteTarget;exports.h = stringifyRouteThreadId;exports.i = channelRouteKey;exports.l = channelRoutesMatchExact;exports.m = resolveChannelRouteTargetWithParser;exports.n = channelRouteDedupeKey;exports.o = channelRouteTargetsMatchExact;exports.p = normalizeRouteThreadId;exports.r = channelRouteIdentityKey;exports.s = channelRouteTargetsShareConversation;exports.t = channelRouteCompactKey;exports.u = channelRoutesShareConversation;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _accountIdBj7l9NI = require("./account-id-Bj7l9NI7.js");
//#region src/plugin-sdk/channel-route.ts
function normalizeRouteThreadId(value) {
  return (0, _stringCoerceBje8XVt.u)(value);
}
function stringifyRouteThreadId(value) {
  const normalized = normalizeRouteThreadId(value);
  return normalized == null ? void 0 : String(normalized);
}
function normalizeChannelRouteRef(input) {
  if (!input) return;
  const channel = (0, _stringCoerceBje8XVt.a)(input.channel);
  const accountId = typeof input.accountId === "string" ? (0, _accountIdBj7l9NI.r)(input.accountId) : void 0;
  const to = (0, _stringCoerceBje8XVt.c)(input.to);
  const rawTo = (0, _stringCoerceBje8XVt.c)(input.rawTo);
  const threadId = normalizeRouteThreadId(input.threadId);
  if (!channel && !to && !accountId && threadId == null) return;
  return {
    ...(channel ? { channel } : {}),
    ...(accountId ? { accountId } : {}),
    ...(to ? { target: {
        to,
        ...(rawTo && rawTo !== to ? { rawTo } : {}),
        ...(input.chatType ? { chatType: input.chatType } : {})
      } } : {}),
    ...(threadId != null ? { thread: {
        id: threadId,
        ...(input.threadKind ? { kind: input.threadKind } : {}),
        ...(input.threadSource ? { source: input.threadSource } : {})
      } } : {})
  };
}
function channelRouteTarget(route) {
  return route?.target?.to;
}
function channelRouteThreadId(route) {
  return route?.thread?.id;
}
function normalizeChannelRouteTarget(input) {
  return input ? normalizeChannelRouteRef(input) : void 0;
}
function resolveChannelRouteTargetWithParser(params) {
  const channel = (0, _stringCoerceBje8XVt.a)(params.channel);
  const rawTo = (0, _stringCoerceBje8XVt.c)(params.rawTarget);
  if (!channel || !rawTo) return null;
  const parsed = params.parseExplicitTarget(channel, rawTo);
  const fallbackThreadId = (0, _stringCoerceBje8XVt.u)(params.fallbackThreadId);
  return {
    channel,
    rawTo,
    to: parsed?.to ?? rawTo,
    threadId: (0, _stringCoerceBje8XVt.u)(parsed?.threadId ?? fallbackThreadId),
    chatType: parsed?.chatType
  };
}
function channelRouteDedupeKey(input) {
  const route = normalizeChannelRouteTarget(input);
  return JSON.stringify([
  route?.channel ?? "",
  route?.target?.to ?? "",
  route?.accountId ?? "",
  stringifyRouteThreadId(route?.thread?.id) ?? ""]
  );
}
/** @deprecated Use `channelRouteDedupeKey`. */
function channelRouteIdentityKey(input) {
  return channelRouteDedupeKey(input);
}
function threadIdsEqual(left, right) {
  return stringifyRouteThreadId(left) === stringifyRouteThreadId(right);
}
function accountsCompatible(left, right) {
  return !left || !right || left === right;
}
function accountsEqual(left, right) {
  return (left ?? "") === (right ?? "");
}
function channelRoutesMatchExact(params) {
  const { left, right } = params;
  if (!left || !right) return false;
  return left.channel === right.channel && left.target?.to === right.target?.to && accountsEqual(left.accountId, right.accountId) && threadIdsEqual(left.thread?.id, right.thread?.id);
}
function channelRoutesShareConversation(params) {
  const { left, right } = params;
  if (!left || !right) return false;
  if (left.channel !== right.channel || left.target?.to !== right.target?.to || !accountsCompatible(left.accountId, right.accountId)) return false;
  if (left.thread?.id == null || right.thread?.id == null) return true;
  return threadIdsEqual(left.thread.id, right.thread.id);
}
function channelRouteTargetsMatchExact(params) {
  return channelRoutesMatchExact({
    left: normalizeChannelRouteTarget(params.left),
    right: normalizeChannelRouteTarget(params.right)
  });
}
function channelRouteTargetsShareConversation(params) {
  return channelRoutesShareConversation({
    left: normalizeChannelRouteTarget(params.left),
    right: normalizeChannelRouteTarget(params.right)
  });
}
function isChannelRouteRef(route) {
  return "target" in route || "thread" in route;
}
function normalizeChannelRouteKeyInput(route) {
  if (!route) return;
  return isChannelRouteRef(route) ? normalizeChannelRouteRef({
    channel: route.channel,
    to: route.target?.to,
    accountId: route.accountId,
    threadId: route.thread?.id
  }) : normalizeChannelRouteTarget(route);
}
function channelRouteCompactKey(route) {
  const normalized = normalizeChannelRouteKeyInput(route);
  if (!normalized?.channel || !normalized.target?.to) return;
  return [
  normalized.channel,
  normalized.target.to,
  normalized.accountId ?? "",
  stringifyRouteThreadId(normalized.thread?.id) ?? ""].
  join("|");
}
/** @deprecated Use `channelRouteCompactKey`. */
function channelRouteKey(route) {
  return channelRouteCompactKey(route);
}
//#endregion /* v9-5aaa2eb9e9b3590a */
