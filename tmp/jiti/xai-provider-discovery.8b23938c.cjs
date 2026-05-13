"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _webSearchProviderCommonByzoAZEn = require("../../web-search-provider-common-ByzoAZEn.js");
require("../../provider-web-search-DbjxPCgG.js");
var _toolAuthShared15erY7Yc = require("../../tool-auth-shared-15erY7Yc.js");
//#region extensions/xai/provider-discovery.ts
const PROVIDER_ID = "xai";
function resolveXaiSyntheticAuth(config) {
  const apiKey = (0, _toolAuthShared15erY7Yc.n)(config)?.apiKey || (0, _webSearchProviderCommonByzoAZEn.p)(["XAI_API_KEY"]);
  return apiKey ? {
    apiKey,
    source: "xAI plugin config",
    mode: "api-key"
  } : void 0;
}
const xaiProviderDiscovery = exports.default = {
  id: PROVIDER_ID,
  label: "xAI",
  docsPath: "/providers/models",
  auth: [],
  resolveSyntheticAuth: ({ config }) => resolveXaiSyntheticAuth(config)
};
//#endregion /* v9-cd555bca229f7042 */
