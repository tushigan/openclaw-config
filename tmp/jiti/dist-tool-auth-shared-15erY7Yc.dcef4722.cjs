"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveFallbackXaiAuth;exports.r = resolveXaiToolApiKey;exports.t = isXaiToolEnabled;var _typesSecretsCL51SR4g = require("./types.secrets-CL51SR4g.js");
var _modelAuthMarkersDBkfxh3_ = require("./model-auth-markers-DBkfxh3_.js");
require("./provider-auth-Kvk9CJPa.js");
var _webSearchProviderCommonByzoAZEn = require("./web-search-provider-common-ByzoAZEn.js");
require("./secret-input-BP7EccAI.js");
var _extensionSharedDUYXCIBS = require("./extension-shared-DUYXCIBS.js");
var _webSearchProviderConfig90N7FtlC = require("./web-search-provider-config-90N7FtlC.js");
require("./provider-web-search-DbjxPCgG.js");
//#region extensions/xai/src/tool-auth-shared.ts
const XAI_API_KEY_ENV_VAR = "XAI_API_KEY";
function readConfiguredOrManagedApiKey(value) {
  const literal = (0, _typesSecretsCL51SR4g.d)(value);
  if (literal) return literal;
  const ref = (0, _typesSecretsCL51SR4g.o)(value);
  return ref ? (0, _modelAuthMarkersDBkfxh3_.h)(ref.source) : void 0;
}
function readLegacyGrokFallbackAuth(cfg) {
  const search = cfg?.tools?.web?.search;
  if (!search || typeof search !== "object") return;
  const grok = search.grok;
  const apiKey = readConfiguredOrManagedApiKey(grok && typeof grok === "object" ? grok.apiKey : void 0);
  return apiKey ? {
    apiKey,
    source: "tools.web.search.grok.apiKey"
  } : void 0;
}
function readConfiguredRuntimeApiKey(value, path, cfg) {
  const resolved = (0, _typesSecretsCL51SR4g.h)({
    value,
    path,
    defaults: cfg?.secrets?.defaults,
    mode: "inspect"
  });
  if (resolved.status === "available") return {
    status: "available",
    value: resolved.value
  };
  if (resolved.status === "missing") return { status: "missing" };
  if (resolved.ref.source !== "env") return { status: "blocked" };
  const envVarName = resolved.ref.id.trim();
  if (envVarName !== XAI_API_KEY_ENV_VAR) return { status: "blocked" };
  if (!(0, _extensionSharedDUYXCIBS.i)({
    cfg,
    provider: resolved.ref.provider,
    id: envVarName
  })) return { status: "blocked" };
  const envValue = (0, _typesSecretsCL51SR4g.d)(process.env[envVarName]);
  return envValue ? {
    status: "available",
    value: envValue
  } : { status: "missing" };
}
function readLegacyGrokApiKeyResult(cfg) {
  const search = cfg?.tools?.web?.search;
  if (!search || typeof search !== "object") return { status: "missing" };
  const grok = search.grok;
  return readConfiguredRuntimeApiKey(grok && typeof grok === "object" ? grok.apiKey : void 0, "tools.web.search.grok.apiKey", cfg);
}
function readPluginXaiWebSearchApiKeyResult(cfg) {
  return readConfiguredRuntimeApiKey((0, _webSearchProviderConfig90N7FtlC.i)(cfg, "xai")?.apiKey, "plugins.entries.xai.config.webSearch.apiKey", cfg);
}
function resolveFallbackXaiAuth(cfg) {
  const pluginApiKey = readConfiguredOrManagedApiKey((0, _webSearchProviderConfig90N7FtlC.i)(cfg, "xai")?.apiKey);
  if (pluginApiKey) return {
    apiKey: pluginApiKey,
    source: "plugins.entries.xai.config.webSearch.apiKey"
  };
  return readLegacyGrokFallbackAuth(cfg);
}
function resolveXaiToolApiKey(params) {
  const runtimePlugin = readPluginXaiWebSearchApiKeyResult(params.runtimeConfig);
  if (runtimePlugin.status === "available") return runtimePlugin.value;
  if (runtimePlugin.status === "blocked") return;
  const runtimeLegacy = readLegacyGrokApiKeyResult(params.runtimeConfig);
  if (runtimeLegacy.status === "available") return runtimeLegacy.value;
  if (runtimeLegacy.status === "blocked") return;
  const sourcePlugin = readPluginXaiWebSearchApiKeyResult(params.sourceConfig);
  if (sourcePlugin.status === "available") return sourcePlugin.value;
  if (sourcePlugin.status === "blocked") return;
  const sourceLegacy = readLegacyGrokApiKeyResult(params.sourceConfig);
  if (sourceLegacy.status === "available") return sourceLegacy.value;
  if (sourceLegacy.status === "blocked") return;
  return (0, _webSearchProviderCommonByzoAZEn.p)([XAI_API_KEY_ENV_VAR]);
}
function isXaiToolEnabled(params) {
  if (params.enabled === false) return false;
  return Boolean(resolveXaiToolApiKey(params));
}
//#endregion /* v9-fc42a4d697564173 */
