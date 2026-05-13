"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.ollamaProviderDiscovery = exports.default = void 0;var _providerBaseUrlBdKwtJTo = require("../../provider-base-url-BdKwtJTo.js");
var _discoveryShared5mFUGF0x = require("../../discovery-shared-5mFUGF0x.js");
//#region extensions/ollama/provider-discovery.ts
function resolveOllamaPluginConfig(ctx) {
  return (ctx.config.plugins?.entries ?? {}).ollama?.config ?? {};
}
async function runOllamaDiscovery(ctx) {
  return await (0, _discoveryShared5mFUGF0x.r)({
    ctx,
    pluginConfig: resolveOllamaPluginConfig(ctx),
    buildProvider: _providerBaseUrlBdKwtJTo.i
  });
}
const ollamaProviderDiscovery = exports.ollamaProviderDiscovery = exports.default = {
  id: _discoveryShared5mFUGF0x.n,
  label: "Ollama",
  docsPath: "/providers/ollama",
  envVars: ["OLLAMA_API_KEY"],
  auth: [],
  resolveSyntheticAuth: ({ provider, providerConfig }) => {
    if (!(0, _discoveryShared5mFUGF0x.i)(providerConfig)) return;
    return {
      apiKey: _discoveryShared5mFUGF0x.t,
      source: `models.providers.${provider ?? "ollama"} (synthetic local key)`,
      mode: "api-key"
    };
  },
  discovery: {
    order: "late",
    run: runOllamaDiscovery
  }
};
//#endregion /* v9-d525f26ca59076ec */
