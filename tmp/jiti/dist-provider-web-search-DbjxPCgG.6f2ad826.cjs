"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveWebSearchProviderCredential;exports.r = resolveCitationRedirectUrl;exports.t = createPluginBackedWebSearchProvider;var _typesSecretsCL51SR4g = require("./types.secrets-CL51SR4g.js");
require("./enable-BLCgq3fU.js");
var _normalizeSecretInputG30DI_5w = require("./normalize-secret-input-G30DI_5w.js");
require("./common-CA61yuMe.js");
require("./external-content-M-sFVDK7.js");
require("./web-shared-cXpllDuo.js");
require("./web-search-provider-common-ByzoAZEn.js");
var _webGuardedFetchZh1Ihtf_ = require("./web-guarded-fetch-Zh1Ihtf_.js");
//#region src/agents/tools/web-search-citation-redirect.ts
const REDIRECT_TIMEOUT_MS = 5e3;
/**
* Resolve a citation redirect URL to its final destination using a HEAD request.
* Returns the original URL if resolution fails or times out.
*/
async function resolveCitationRedirectUrl(url) {
  try {
    return await (0, _webGuardedFetchZh1Ihtf_.r)({
      url,
      init: { method: "HEAD" },
      timeoutMs: REDIRECT_TIMEOUT_MS
    }, async ({ finalUrl }) => finalUrl || url);
  } catch {
    return url;
  }
}
//#endregion
//#region src/agents/tools/web-search-provider-credentials.ts
function resolveWebSearchProviderCredential(params) {
  const fromConfig = (0, _normalizeSecretInputG30DI_5w.n)((0, _typesSecretsCL51SR4g.d)(params.credentialValue));
  if (fromConfig) return fromConfig;
  const credentialRef = (0, _typesSecretsCL51SR4g.m)({ value: params.credentialValue }).ref;
  if (credentialRef) {
    if (credentialRef.source !== "env") return;
    const fromEnvRef = (0, _normalizeSecretInputG30DI_5w.n)(process.env[credentialRef.id]);
    if (fromEnvRef) return fromEnvRef;
    return;
  }
  for (const envVar of params.envVars) {
    const fromEnv = (0, _normalizeSecretInputG30DI_5w.n)(process.env[envVar]);
    if (fromEnv) return fromEnv;
  }
}
//#endregion
//#region src/plugin-sdk/provider-web-search.ts
/**
* @deprecated Implement provider-owned `createTool(...)` directly on the
* returned WebSearchProviderPlugin instead of routing through core.
*/
function createPluginBackedWebSearchProvider(provider) {
  return {
    ...provider,
    createTool: () => {
      throw new Error(`createPluginBackedWebSearchProvider(${provider.id}) is no longer supported. Define provider-owned createTool(...) directly in the extension's WebSearchProviderPlugin.`);
    }
  };
}
//#endregion /* v9-e9aee9a41116770b */
