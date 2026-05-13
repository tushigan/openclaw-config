"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = listPotentialConfiguredChannelPresenceSignals;exports.i = listPotentialConfiguredChannelIds;exports.n = hasPotentialConfiguredChannels;exports.o = collectConfiguredAgentHarnessRuntimes;exports.r = listExplicitlyDisabledChannelIdsForConfig;exports.t = hasMeaningfulChannelConfig;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _pathsC1_Y0cDn = require("./paths-C1_Y0cDn.js");
var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
var _packageStateProbesAnoN2cCB = require("./package-state-probes-AnoN2cCB.js");
var _agentRuntimePolicyCOQbqCOp = require("./agent-runtime-policy-COQbqCOp.js");
var _bootstrapRegistryCLMjz7B = require("./bootstrap-registry-C-lMjz7B.js");
var _channelTargetCO44lwZF = require("./channel-target-CO44lwZF.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodeOs = _interopRequireDefault(require("node:os"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/agents/harness-runtimes.ts
function collectConfiguredAgentHarnessRuntimes(config, env) {
  const runtimes = /* @__PURE__ */new Set();
  const pushRuntime = (value) => {
    if (typeof value !== "string") return;
    const normalized = (0, _stringCoerceBje8XVt.s)(value);
    if (!normalized || normalized === "auto" || normalized === "pi") return;
    runtimes.add(normalized);
  };
  pushRuntime((0, _agentRuntimePolicyCOQbqCOp.t)(config.agents?.defaults)?.id);
  if (Array.isArray(config.agents?.list)) for (const agent of config.agents.list) {
    if (!(0, _utilsD5swhEXt.c)(agent)) continue;
    pushRuntime((0, _agentRuntimePolicyCOQbqCOp.t)(agent)?.id);
  }
  pushRuntime(env.OPENCLAW_AGENT_RUNTIME);
  return [...runtimes].toSorted((left, right) => left.localeCompare(right));
}
//#endregion
//#region src/channels/plugins/persisted-auth-state.ts
function listBundledChannelIdsWithPersistedAuthState() {
  return (0, _packageStateProbesAnoN2cCB.n)("persistedAuthState");
}
function hasBundledChannelPersistedAuthState(params) {
  return (0, _packageStateProbesAnoN2cCB.t)({
    metadataKey: "persistedAuthState",
    channelId: params.channelId,
    cfg: params.cfg,
    env: params.env
  });
}
//#endregion
//#region src/channels/config-presence.ts
const IGNORED_CHANNEL_CONFIG_KEYS = new Set(["defaults", "modelByChannel"]);
function hasMeaningfulChannelConfig(value) {
  if (!(0, _utilsD5swhEXt.c)(value)) return false;
  return Object.keys(value).some((key) => key !== "enabled");
}
function listExplicitlyDisabledChannelIdsForConfig(cfg) {
  const channels = (0, _utilsD5swhEXt.c)(cfg.channels) ? cfg.channels : null;
  if (!channels) return [];
  return Object.entries(channels).filter(([, value]) => (0, _utilsD5swhEXt.c)(value) && value.enabled === false).map(([channelId]) => (0, _stringCoerceBje8XVt.s)(channelId)).filter((channelId) => Boolean(channelId));
}
function listChannelEnvPrefixes(channelIds) {
  return channelIds.map((channelId) => [`${channelId.replace(/[^a-z0-9]+/gi, "_").toUpperCase()}_`, channelId]);
}
function hasPersistedChannelState(env) {
  return _nodeFs.default.existsSync((0, _pathsC1_Y0cDn.v)(env, _nodeOs.default.homedir));
}
let persistedAuthStateChannelIds = null;
function listPersistedAuthStateChannelIds(options) {
  const override = options.persistedAuthStateProbe?.listChannelIds();
  if (override) return override;
  if (persistedAuthStateChannelIds) return persistedAuthStateChannelIds;
  persistedAuthStateChannelIds = listBundledChannelIdsWithPersistedAuthState();
  return persistedAuthStateChannelIds;
}
function hasPersistedAuthState(params) {
  const override = params.options.persistedAuthStateProbe;
  if (override) return override.hasState(params);
  return hasBundledChannelPersistedAuthState(params);
}
function listPotentialConfiguredChannelIds(cfg, env = process.env, options = {}) {
  return [...new Set(listPotentialConfiguredChannelPresenceSignals(cfg, env, options).map((signal) => signal.channelId))];
}
function listPotentialConfiguredChannelPresenceSignals(cfg, env = process.env, options = {}) {
  const signals = [];
  const seenSignals = /* @__PURE__ */new Set();
  const addSignal = (channelId, source) => {
    const key = `${source}:${channelId}`;
    if (seenSignals.has(key)) return;
    seenSignals.add(key);
    signals.push({
      channelId,
      source
    });
  };
  const configuredChannelIds = /* @__PURE__ */new Set();
  const channelEnvPrefixes = listChannelEnvPrefixes(options.channelIds ?? (0, _bootstrapRegistryCLMjz7B.i)(env));
  const channels = (0, _utilsD5swhEXt.c)(cfg.channels) ? cfg.channels : null;
  if (channels) for (const [key, value] of Object.entries(channels)) {
    if (IGNORED_CHANNEL_CONFIG_KEYS.has(key)) continue;
    if (hasMeaningfulChannelConfig(value)) {
      configuredChannelIds.add(key);
      addSignal(key, "config");
    }
  }
  for (const [key, value] of Object.entries(env)) {
    if (!(0, _channelTargetCO44lwZF.i)(value)) continue;
    for (const [prefix, channelId] of channelEnvPrefixes) if (key.startsWith(prefix)) {
      configuredChannelIds.add(channelId);
      addSignal(channelId, "env");
    }
  }
  if (options.includePersistedAuthState !== false && hasPersistedChannelState(env)) {
    for (const channelId of listPersistedAuthStateChannelIds(options)) if (hasPersistedAuthState({
      channelId,
      cfg,
      env,
      options
    })) {
      configuredChannelIds.add(channelId);
      addSignal(channelId, "persisted-auth");
    }
  }
  return signals.filter((signal) => configuredChannelIds.has(signal.channelId));
}
function hasEnvConfiguredChannel(cfg, env, options = {}) {
  const channelEnvPrefixes = listChannelEnvPrefixes(options.channelIds ?? (0, _bootstrapRegistryCLMjz7B.i)(env));
  for (const [key, value] of Object.entries(env)) {
    if (!(0, _channelTargetCO44lwZF.i)(value)) continue;
    if (channelEnvPrefixes.some(([prefix]) => key.startsWith(prefix))) return true;
  }
  if (options.includePersistedAuthState === false || !hasPersistedChannelState(env)) return false;
  return listPersistedAuthStateChannelIds(options).some((channelId) => hasPersistedAuthState({
    channelId,
    cfg,
    env,
    options
  }));
}
function hasPotentialConfiguredChannels(cfg, env = process.env, options = {}) {
  const channels = (0, _utilsD5swhEXt.c)(cfg?.channels) ? cfg.channels : null;
  if (channels) for (const [key, value] of Object.entries(channels)) {
    if (IGNORED_CHANNEL_CONFIG_KEYS.has(key)) continue;
    if (hasMeaningfulChannelConfig(value)) return true;
  }
  return hasEnvConfiguredChannel(cfg ?? {}, env, options);
}
//#endregion /* v9-4574c3bcdafb1899 */
