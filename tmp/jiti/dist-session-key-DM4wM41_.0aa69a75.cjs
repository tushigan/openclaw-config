"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveSessionKey;exports.t = deriveSessionKey;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
var _sessionKeyC0K0uhmG = require("./session-key-C0K0uhmG.js");
var _messageChannelB1O_CztY = require("./message-channel-B1O_CztY.js");
var _registryBkuUNjzB = require("./registry-BkuUNjzB.js");
var _storeDvxAjGkI = require("./store-DvxAjGkI.js");
require("./plugins-C729ZIvi.js");
//#region src/config/sessions/explicit-session-key-normalization.ts
function resolveExplicitSessionKeyNormalizerCandidates(sessionKey, ctx) {
  const normalizedProvider = (0, _stringCoerceBje8XVt.s)(ctx.Provider);
  const normalizedSurface = (0, _stringCoerceBje8XVt.s)(ctx.Surface);
  const normalizedFrom = (0, _stringCoerceBje8XVt.a)(ctx.From);
  const candidates = /* @__PURE__ */new Set();
  const maybeAdd = (value) => {
    const normalized = (0, _messageChannelB1O_CztY.u)(value);
    if (normalized) candidates.add(normalized);
  };
  maybeAdd(normalizedSurface);
  maybeAdd(normalizedProvider);
  maybeAdd(normalizedFrom.split(":", 1)[0]);
  for (const plugin of (0, _registryBkuUNjzB.i)()) {
    const pluginId = (0, _messageChannelB1O_CztY.u)(plugin.id);
    if (!pluginId) continue;
    if (sessionKey.startsWith(`${pluginId}:`) || sessionKey.includes(`:${pluginId}:`)) candidates.add(pluginId);
  }
  return [...candidates];
}
function normalizeExplicitSessionKey(sessionKey, ctx) {
  const normalized = (0, _stringCoerceBje8XVt.a)(sessionKey);
  for (const channelId of resolveExplicitSessionKeyNormalizerCandidates(normalized, ctx)) {
    const normalize = (0, _registryBkuUNjzB.n)(channelId)?.messaging?.normalizeExplicitSessionKey;
    const next = normalize?.({
      sessionKey: normalized,
      ctx
    });
    if (typeof next === "string" && next.trim()) return (0, _stringCoerceBje8XVt.a)(next);
  }
  return normalized;
}
//#endregion
//#region src/config/sessions/session-key.ts
function deriveSessionKey(scope, ctx) {
  if (scope === "global") return "global";
  const resolvedGroup = (0, _storeDvxAjGkI.v)(ctx);
  if (resolvedGroup) return resolvedGroup.key;
  return (ctx.From ? (0, _utilsD5swhEXt.l)(ctx.From) : "") || "unknown";
}
/**
* Resolve the session key with a canonical direct-chat bucket (default: "main").
* All non-group direct chats collapse to this bucket; groups stay isolated.
*/
function resolveSessionKey(scope, ctx, mainKey, agentId = _sessionKeyC0K0uhmG.t) {
  const explicit = ctx.SessionKey?.trim();
  if (explicit) return normalizeExplicitSessionKey(explicit, ctx);
  const raw = deriveSessionKey(scope, ctx);
  if (scope === "global") return raw;
  const canonicalAgentId = (0, _sessionKeyC0K0uhmG.c)(agentId);
  const canonical = (0, _sessionKeyC0K0uhmG.r)({
    agentId: canonicalAgentId,
    mainKey: (0, _sessionKeyC0K0uhmG.l)(mainKey)
  });
  if (!(raw.includes(":group:") || raw.includes(":channel:"))) return canonical;
  return `agent:${canonicalAgentId}:${raw}`;
}
//#endregion /* v9-5fb60f25bc4e0d66 */
