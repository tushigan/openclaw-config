"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = collectConfiguredModelRefs;exports.t = void 0;var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
//#region src/config/model-refs.ts
const AGENT_MODEL_CONFIG_KEYS = exports.t = [
"model",
"imageModel",
"imageGenerationModel",
"videoGenerationModel",
"musicGenerationModel",
"pdfModel"];

function collectConfiguredModelRefs(config, options = {}) {
  const refs = [];
  const pushModelRef = (path, value) => {
    if (typeof value === "string" && value.trim()) refs.push({
      path,
      value: value.trim()
    });
  };
  const collectModelConfig = (path, value) => {
    if (typeof value === "string") {
      pushModelRef(path, value);
      return;
    }
    if (!(0, _utilsD5swhEXt.c)(value)) return;
    pushModelRef(`${path}.primary`, value.primary);
    if (Array.isArray(value.fallbacks)) for (const [index, entry] of value.fallbacks.entries()) pushModelRef(`${path}.fallbacks.${index}`, entry);
  };
  const collectFromAgent = (path, agent) => {
    if (!(0, _utilsD5swhEXt.c)(agent)) return;
    for (const key of AGENT_MODEL_CONFIG_KEYS) collectModelConfig(`${path}.${key}`, agent[key]);
    if ((0, _utilsD5swhEXt.c)(agent.models)) for (const modelRef of Object.keys(agent.models)) pushModelRef(`${path}.models.${modelRef}`, modelRef);
  };
  const root = (0, _utilsD5swhEXt.c)(config) ? config : {};
  const agents = (0, _utilsD5swhEXt.c)(root.agents) ? root.agents : {};
  collectFromAgent("agents.defaults", agents.defaults);
  if (Array.isArray(agents.list)) for (const [index, entry] of agents.list.entries()) collectFromAgent(`agents.list.${index}`, entry);
  if (options.includeChannelModelOverrides !== false) {
    const channels = (0, _utilsD5swhEXt.c)(root.channels) ? root.channels : {};
    const modelByChannel = (0, _utilsD5swhEXt.c)(channels.modelByChannel) ? channels.modelByChannel : {};
    for (const [channelId, channelMap] of Object.entries(modelByChannel)) {
      if (!(0, _utilsD5swhEXt.c)(channelMap)) continue;
      for (const [targetId, modelRef] of Object.entries(channelMap)) pushModelRef(`channels.modelByChannel.${channelId}.${targetId}`, modelRef);
    }
  }
  return refs;
}
//#endregion /* v9-414a83a9cbd7329b */
