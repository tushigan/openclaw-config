"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = resolveThreadBindingIdleTimeoutMs;exports.c = resolveThreadBindingMaxAgeMsForChannel;exports.d = resolveThreadBindingsEnabled;exports.f = supportsAutomaticThreadBindingSpawn;exports.i = resolveThreadBindingEffectiveExpiresAt;exports.l = resolveThreadBindingPlacementForCurrentContext;exports.n = formatThreadBindingSpawnDisabledError;exports.o = resolveThreadBindingIdleTimeoutMsForChannel;exports.r = requiresNativeThreadContextForThreadHere;exports.s = resolveThreadBindingMaxAgeMs;exports.t = formatThreadBindingDisabledError;exports.u = resolveThreadBindingSpawnPolicy;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _accountIdBj7l9NI = require("./account-id-Bj7l9NI7.js");
var _registryBkuUNjzB = require("./registry-BkuUNjzB.js");
require("./plugins-C729ZIvi.js");
var _threadBindingLifecycleUnFXujT = require("./thread-binding-lifecycle-UnFXuj-t.js");
var _threadBindingApiCFAq5PKE = require("./thread-binding-api-CFAq5PKE.js");
//#region src/channels/thread-bindings-policy.ts
const DEFAULT_THREAD_BINDING_IDLE_HOURS = 24;
const DEFAULT_THREAD_BINDING_MAX_AGE_HOURS = 0;
function normalizeChannelId(value) {
  return (0, _stringCoerceBje8XVt.a)(value);
}
function supportsAutomaticThreadBindingSpawn(channel) {
  return resolveDefaultTopLevelPlacement(channel) === "child";
}
function requiresNativeThreadContextForThreadHere(channel) {
  return resolveDefaultTopLevelPlacement(channel) === "child";
}
function resolveThreadBindingPlacementForCurrentContext(params) {
  if (resolveDefaultTopLevelPlacement(params.channel) !== "child") return "current";
  return params.threadId ? "current" : "child";
}
function resolveDefaultTopLevelPlacement(channel) {
  const normalized = normalizeChannelId(channel);
  if (!normalized) return "current";
  return (0, _registryBkuUNjzB.n)(normalized)?.conversationBindings?.defaultTopLevelPlacement ?? (0, _threadBindingApiCFAq5PKE.t)(normalized) ?? "current";
}
function normalizeBoolean(value) {
  if (typeof value !== "boolean") return;
  return value;
}
function normalizeThreadBindingHours(raw) {
  if (typeof raw !== "number" || !Number.isFinite(raw)) return;
  if (raw < 0) return;
  return raw;
}
function resolveThreadBindingIdleTimeoutMs(params) {
  const idleHours = normalizeThreadBindingHours(params.channelIdleHoursRaw) ?? normalizeThreadBindingHours(params.sessionIdleHoursRaw) ?? DEFAULT_THREAD_BINDING_IDLE_HOURS;
  return Math.floor(idleHours * 60 * 60 * 1e3);
}
function resolveThreadBindingMaxAgeMs(params) {
  const maxAgeHours = normalizeThreadBindingHours(params.channelMaxAgeHoursRaw) ?? normalizeThreadBindingHours(params.sessionMaxAgeHoursRaw) ?? DEFAULT_THREAD_BINDING_MAX_AGE_HOURS;
  return Math.floor(maxAgeHours * 60 * 60 * 1e3);
}
function resolveThreadBindingEffectiveExpiresAt(params) {
  return (0, _threadBindingLifecycleUnFXujT.t)(params).expiresAt;
}
function resolveThreadBindingsEnabled(params) {
  return normalizeBoolean(params.channelEnabledRaw) ?? normalizeBoolean(params.sessionEnabledRaw) ?? true;
}
function resolveChannelThreadBindings(params) {
  const channelConfig = params.cfg.channels?.[params.channel];
  const accountConfig = channelConfig?.accounts?.[params.accountId];
  return {
    root: channelConfig?.threadBindings,
    account: accountConfig?.threadBindings
  };
}
function resolveSpawnFlagKey(kind) {
  return kind === "subagent" ? "spawnSubagentSessions" : "spawnAcpSessions";
}
function normalizeSpawnContext(value) {
  return value === "isolated" || value === "fork" ? value : void 0;
}
function resolveThreadBindingSpawnPolicy(params) {
  const channel = normalizeChannelId(params.channel);
  const accountId = (0, _accountIdBj7l9NI.n)(params.accountId);
  const { root, account } = resolveChannelThreadBindings({
    cfg: params.cfg,
    channel,
    accountId
  });
  const enabled = normalizeBoolean(account?.enabled) ?? normalizeBoolean(root?.enabled) ?? normalizeBoolean(params.cfg.session?.threadBindings?.enabled) ?? true;
  const spawnFlagKey = resolveSpawnFlagKey(params.kind);
  return {
    channel,
    accountId,
    enabled,
    spawnEnabled: normalizeBoolean(account?.[spawnFlagKey]) ?? normalizeBoolean(account?.spawnSessions) ?? normalizeBoolean(root?.[spawnFlagKey]) ?? normalizeBoolean(root?.spawnSessions) ?? normalizeBoolean(params.cfg.session?.threadBindings?.spawnSessions) ?? true,
    defaultSpawnContext: normalizeSpawnContext(account?.defaultSpawnContext) ?? normalizeSpawnContext(root?.defaultSpawnContext) ?? normalizeSpawnContext(params.cfg.session?.threadBindings?.defaultSpawnContext) ?? "fork"
  };
}
function resolveThreadBindingIdleTimeoutMsForChannel(params) {
  const { root, account } = resolveThreadBindingChannelScope(params);
  return resolveThreadBindingIdleTimeoutMs({
    channelIdleHoursRaw: account?.idleHours ?? root?.idleHours,
    sessionIdleHoursRaw: params.cfg.session?.threadBindings?.idleHours
  });
}
function resolveThreadBindingMaxAgeMsForChannel(params) {
  const { root, account } = resolveThreadBindingChannelScope(params);
  return resolveThreadBindingMaxAgeMs({
    channelMaxAgeHoursRaw: account?.maxAgeHours ?? root?.maxAgeHours,
    sessionMaxAgeHoursRaw: params.cfg.session?.threadBindings?.maxAgeHours
  });
}
function resolveThreadBindingChannelScope(params) {
  const channel = normalizeChannelId(params.channel);
  const accountId = (0, _accountIdBj7l9NI.n)(params.accountId);
  return resolveChannelThreadBindings({
    cfg: params.cfg,
    channel,
    accountId
  });
}
function formatThreadBindingDisabledError(params) {
  return `Thread bindings are disabled for ${params.channel} (set channels.${params.channel}.threadBindings.enabled=true to override for this account, or session.threadBindings.enabled=true globally).`;
}
function formatThreadBindingSpawnDisabledError(params) {
  return `Thread-bound session spawns are disabled for ${params.channel} (set channels.${params.channel}.threadBindings.spawnSessions=true to enable).`;
}
//#endregion /* v9-8100474b4af5b972 */
