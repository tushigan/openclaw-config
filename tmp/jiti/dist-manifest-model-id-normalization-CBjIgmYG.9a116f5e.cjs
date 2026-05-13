"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = normalizeProviderModelIdWithManifest;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _pluginMetadataSnapshotMEvRUosy = require("./plugin-metadata-snapshot-mEvRUosy.js");
var _currentPluginMetadataSnapshotCBeGKry = require("./current-plugin-metadata-snapshot-CBe-gKry.js");
var _runtimeStateNl5PFZKO = require("./runtime-state-Nl5PFZKO.js");
//#region src/plugins/manifest-model-id-normalization.ts
function collectManifestModelIdNormalizationPolicies(plugins) {
  const policies = /* @__PURE__ */new Map();
  for (const plugin of plugins) for (const [provider, policy] of Object.entries(plugin.modelIdNormalization?.providers ?? {})) policies.set((0, _stringCoerceBje8XVt.a)(provider), policy);
  return policies;
}
let cachedPolicies;
function resolveMetadataSnapshotForPolicies(params = {}) {
  const env = params.env ?? process.env;
  const workspaceDir = params.workspaceDir ?? (0, _runtimeStateNl5PFZKO.n)();
  const current = (0, _currentPluginMetadataSnapshotCBeGKry.n)({
    config: params.config,
    env,
    workspaceDir
  });
  if (current) return {
    snapshot: current,
    cacheable: true
  };
  return {
    snapshot: (0, _pluginMetadataSnapshotMEvRUosy.r)({
      config: params.config ?? {},
      env,
      workspaceDir
    }),
    cacheable: false
  };
}
function loadManifestModelIdNormalizationPolicies(params = {}) {
  if (params.plugins) return collectManifestModelIdNormalizationPolicies(params.plugins);
  const { snapshot, cacheable } = resolveMetadataSnapshotForPolicies(params);
  const configFingerprint = snapshot.configFingerprint;
  if (cacheable && configFingerprint && cachedPolicies?.configFingerprint === configFingerprint) return cachedPolicies.policies;
  const policies = collectManifestModelIdNormalizationPolicies(snapshot.plugins);
  if (cacheable && configFingerprint) cachedPolicies = {
    configFingerprint,
    policies
  };
  return policies;
}
function resolveManifestModelIdNormalizationPolicy(provider, params = {}) {
  const providerId = (0, _stringCoerceBje8XVt.a)(provider);
  return loadManifestModelIdNormalizationPolicies(params).get(providerId);
}
function hasProviderPrefix(modelId) {
  return modelId.includes("/");
}
function formatPrefixedModelId(prefix, modelId) {
  return `${prefix.replace(/\/+$/u, "")}/${modelId.replace(/^\/+/u, "")}`;
}
function normalizeProviderModelIdWithManifest(params) {
  const policy = resolveManifestModelIdNormalizationPolicy(params.provider, params);
  if (!policy) return;
  let modelId = params.context.modelId.trim();
  if (!modelId) return modelId;
  for (const prefix of policy.stripPrefixes ?? []) {
    const normalizedPrefix = (0, _stringCoerceBje8XVt.a)(prefix);
    if (normalizedPrefix && (0, _stringCoerceBje8XVt.a)(modelId).startsWith(normalizedPrefix)) {
      modelId = modelId.slice(prefix.length);
      break;
    }
  }
  modelId = policy.aliases?.[(0, _stringCoerceBje8XVt.a)(modelId)] ?? modelId;
  if (!hasProviderPrefix(modelId)) {
    for (const rule of policy.prefixWhenBareAfterAliasStartsWith ?? []) if ((0, _stringCoerceBje8XVt.a)(modelId).startsWith(rule.modelPrefix.toLowerCase())) return formatPrefixedModelId(rule.prefix, modelId);
    if (policy.prefixWhenBare) return formatPrefixedModelId(policy.prefixWhenBare, modelId);
  }
  return modelId;
}
//#endregion /* v9-fd6d7dd2b0c0e2cf */
