"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = buildMoonshotProvider;exports.i = applyMoonshotNativeStreamingUsageCompat;exports.n = void 0;exports.o = isNativeMoonshotBaseUrl;exports.t = exports.r = void 0;var _providerCatalogSharedCYN2NIkQ = require("./provider-catalog-shared-CYN2NIkQ.js");
//#region extensions/moonshot/openclaw.plugin.json
var modelCatalog = {
  "providers": { "moonshot": {
      "baseUrl": "https://api.moonshot.ai/v1",
      "api": "openai-completions",
      "models": [
      {
        "id": "kimi-k2.6",
        "name": "Kimi K2.6",
        "input": ["text", "image"],
        "contextWindow": 262144,
        "maxTokens": 262144,
        "cost": {
          "input": .95,
          "output": 4,
          "cacheRead": .16,
          "cacheWrite": 0
        }
      },
      {
        "id": "kimi-k2.5",
        "name": "Kimi K2.5",
        "input": ["text", "image"],
        "contextWindow": 262144,
        "maxTokens": 262144,
        "cost": {
          "input": .6,
          "output": 3,
          "cacheRead": .1,
          "cacheWrite": 0
        }
      },
      {
        "id": "kimi-k2-thinking",
        "name": "Kimi K2 Thinking",
        "reasoning": true,
        "input": ["text"],
        "contextWindow": 262144,
        "maxTokens": 262144,
        "cost": {
          "input": 0,
          "output": 0,
          "cacheRead": 0,
          "cacheWrite": 0
        }
      },
      {
        "id": "kimi-k2-thinking-turbo",
        "name": "Kimi K2 Thinking Turbo",
        "reasoning": true,
        "input": ["text"],
        "contextWindow": 262144,
        "maxTokens": 262144,
        "cost": {
          "input": 0,
          "output": 0,
          "cacheRead": 0,
          "cacheWrite": 0
        }
      },
      {
        "id": "kimi-k2-turbo",
        "name": "Kimi K2 Turbo",
        "input": ["text"],
        "contextWindow": 256e3,
        "maxTokens": 16384,
        "cost": {
          "input": 0,
          "output": 0,
          "cacheRead": 0,
          "cacheWrite": 0
        }
      }]

    } },
  "discovery": { "moonshot": "static" }
};
//#endregion
//#region extensions/moonshot/provider-catalog.ts
const MOONSHOT_BASE_URL = exports.t = "https://api.moonshot.ai/v1";
const MOONSHOT_CN_BASE_URL = exports.n = "https://api.moonshot.cn/v1";
const MOONSHOT_DEFAULT_MODEL_ID = exports.r = "kimi-k2.6";
function isNativeMoonshotBaseUrl(baseUrl) {
  return (0, _providerCatalogSharedCYN2NIkQ.i)({
    providerId: "moonshot",
    baseUrl
  });
}
function applyMoonshotNativeStreamingUsageCompat(provider) {
  return (0, _providerCatalogSharedCYN2NIkQ.t)({
    providerId: "moonshot",
    providerConfig: provider
  });
}
function buildMoonshotProvider() {
  return (0, _providerCatalogSharedCYN2NIkQ.n)({
    providerId: "moonshot",
    catalog: modelCatalog.providers.moonshot
  });
}
//#endregion /* v9-57284f7e350b90a3 */
