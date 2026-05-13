"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = buildTokenHubModelDefinition;exports.t = exports.r = exports.n = void 0;var _providerCatalogSharedCYN2NIkQ = require("./provider-catalog-shared-CYN2NIkQ.js");
//#region extensions/tencent/openclaw.plugin.json
var modelCatalog = {
  "providers": { "tencent-tokenhub": {
      "baseUrl": "https://tokenhub.tencentmaas.com/v1",
      "api": "openai-completions",
      "models": [{
        "id": "hy3-preview",
        "name": "Hy3 preview (TokenHub)",
        "reasoning": true,
        "input": ["text"],
        "contextWindow": 256e3,
        "maxTokens": 64e3,
        "cost": {
          "input": .176,
          "output": .587,
          "cacheRead": .059,
          "cacheWrite": 0,
          "tieredPricing": [
          {
            "input": .176,
            "output": .587,
            "cacheRead": .059,
            "cacheWrite": 0,
            "range": [0, 16e3]
          },
          {
            "input": .235,
            "output": .939,
            "cacheRead": .088,
            "cacheWrite": 0,
            "range": [16e3, 32e3]
          },
          {
            "input": .293,
            "output": 1.173,
            "cacheRead": .117,
            "cacheWrite": 0,
            "range": [32e3]
          }]

        },
        "compat": {
          "supportsUsageInStreaming": true,
          "supportsReasoningEffort": true
        }
      }]
    } },
  "discovery": { "tencent-tokenhub": "static" }
};
//#endregion
//#region extensions/tencent/models.ts
const TOKENHUB_PROVIDER_ID = exports.r = "tencent-tokenhub";
const TOKENHUB_MANIFEST_PROVIDER = (0, _providerCatalogSharedCYN2NIkQ.n)({
  providerId: TOKENHUB_PROVIDER_ID,
  catalog: modelCatalog.providers[TOKENHUB_PROVIDER_ID]
});
const TOKENHUB_BASE_URL = exports.t = TOKENHUB_MANIFEST_PROVIDER.baseUrl;
const TOKENHUB_MODEL_CATALOG = exports.n = TOKENHUB_MANIFEST_PROVIDER.models;
function buildTokenHubModelDefinition(model) {
  return {
    ...model,
    api: "openai-completions"
  };
}
//#endregion /* v9-c5deb4394f8777a4 */
