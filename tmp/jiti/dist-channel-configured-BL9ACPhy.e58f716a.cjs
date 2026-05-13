"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = isStaticallyChannelConfigured;exports.t = isChannelConfigured;var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
var _channelEnvVarsD7WdYxF = require("./channel-env-vars-D7WdYxF2.js");
var _packageStateProbesAnoN2cCB = require("./package-state-probes-AnoN2cCB.js");
var _bootstrapRegistryCLMjz7B = require("./bootstrap-registry-C-lMjz7B.js");
//#region src/channels/plugins/configured-state.ts
function hasBundledChannelConfiguredState(params) {
  return (0, _packageStateProbesAnoN2cCB.t)({
    metadataKey: "configuredState",
    channelId: params.channelId,
    cfg: params.cfg,
    env: params.env
  });
}
//#endregion
//#region src/config/channel-configured-shared.ts
function resolveChannelConfigRecord(cfg, channelId) {
  const entry = cfg.channels?.[channelId];
  return (0, _utilsD5swhEXt.c)(entry) ? entry : null;
}
function hasMeaningfulChannelConfigShallow(value) {
  if (!(0, _utilsD5swhEXt.c)(value)) return false;
  return Object.keys(value).some((key) => key !== "enabled");
}
function isStaticallyChannelConfigured(cfg, channelId, env = process.env) {
  for (const envVar of (0, _channelEnvVarsD7WdYxF.t)(channelId, {
    config: cfg,
    env
  })) if (typeof env[envVar] === "string" && env[envVar].trim().length > 0) return true;
  return hasMeaningfulChannelConfigShallow(resolveChannelConfigRecord(cfg, channelId));
}
//#endregion
//#region src/config/channel-configured.ts
function isChannelConfigured(cfg, channelId, env = process.env) {
  if (hasMeaningfulChannelConfigShallow(resolveChannelConfigRecord(cfg, channelId))) return true;
  if (hasBundledChannelConfiguredState({
    channelId,
    cfg,
    env
  })) return true;
  const plugin = (0, _bootstrapRegistryCLMjz7B.t)(channelId);
  return Boolean(plugin?.config?.hasConfiguredState?.({
    cfg,
    env
  }));
}
//#endregion /* v9-41065a999986d1bf */
