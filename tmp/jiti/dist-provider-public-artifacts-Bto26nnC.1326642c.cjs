"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = resolveBundledProviderPolicySurface;var _bundledDirDL2yDGTU = require("./bundled-dir-DL2yDGTU.js");
var _manifestRegistryBiAsJcRZ = require("./manifest-registry-BiAsJcRZ.js");
var _providerIdDIRgKpoh = require("./provider-id-DIRgKpoh.js");
var _publicSurfaceLoaderDAC6GNWm = require("./public-surface-loader-DAC6GNWm.js");
//#region src/plugins/provider-public-artifacts.ts
const PROVIDER_POLICY_ARTIFACT_CANDIDATES = ["provider-policy-api.js"];
function hasProviderPolicyHook(mod) {
  return typeof mod.normalizeConfig === "function" || typeof mod.applyConfigDefaults === "function" || typeof mod.resolveConfigApiKey === "function" || typeof mod.resolveThinkingProfile === "function";
}
function tryLoadBundledProviderPolicySurface(pluginId) {
  for (const artifactBasename of PROVIDER_POLICY_ARTIFACT_CANDIDATES) try {
    const mod = (0, _publicSurfaceLoaderDAC6GNWm.t)({
      dirName: pluginId,
      artifactBasename
    });
    if (hasProviderPolicyHook(mod)) return mod;
  } catch (error) {
    if (error instanceof Error && error.message.startsWith("Unable to resolve bundled plugin public surface ")) continue;
    throw error;
  }
  return null;
}
function resolveBundledProviderPolicyPluginId(providerId, options = {}) {
  const normalizedProviderId = (0, _providerIdDIRgKpoh.r)(providerId);
  if (!normalizedProviderId) return null;
  if (!(0, _bundledDirDL2yDGTU.n)()) return null;
  const registry = options.manifestRegistry ?? (0, _manifestRegistryBiAsJcRZ.t)();
  for (const plugin of registry.plugins.toSorted((left, right) => left.id.localeCompare(right.id))) {
    if (plugin.origin !== "bundled") continue;
    if (plugin.providers.some((provider) => (0, _providerIdDIRgKpoh.r)(provider) === normalizedProviderId)) return plugin.id;
  }
  return null;
}
function resolveBundledProviderPolicySurface(providerId, options = {}) {
  const normalizedProviderId = (0, _providerIdDIRgKpoh.r)(providerId);
  if (!normalizedProviderId) return null;
  return tryLoadBundledProviderPolicySurface(normalizedProviderId) ?? tryLoadBundledProviderPolicySurface(resolveBundledProviderPolicyPluginId(normalizedProviderId, options) ?? normalizedProviderId);
}
//#endregion /* v9-b4f09a07dd2e6013 */
