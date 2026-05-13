"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = exports.anthropicVertexProviderDiscovery = void 0;var _regionZm4pn72t = require("../../region-zm4pn72t.js");
var _providerCatalogBP039j_D = require("../../provider-catalog-BP039j_D.js");
//#region extensions/anthropic-vertex/provider-discovery.ts
const PROVIDER_ID = "anthropic-vertex";
const GCP_VERTEX_CREDENTIALS_MARKER = "gcp-vertex-credentials";
function mergeImplicitAnthropicVertexProvider(params) {
  const { existing, implicit } = params;
  if (!existing) return implicit;
  return {
    ...implicit,
    ...existing,
    models: Array.isArray(existing.models) && existing.models.length > 0 ? existing.models : implicit.models
  };
}
function resolveImplicitAnthropicVertexProvider(params) {
  const env = params?.env ?? process.env;
  if (!(0, _regionZm4pn72t.t)(env)) return null;
  return (0, _providerCatalogBP039j_D.n)({ env });
}
async function runAnthropicVertexCatalog(ctx) {
  const implicit = resolveImplicitAnthropicVertexProvider({ env: ctx.env });
  if (!implicit) return null;
  return { provider: mergeImplicitAnthropicVertexProvider({
      existing: ctx.config.models?.providers?.[PROVIDER_ID],
      implicit
    }) };
}
const anthropicVertexProviderDiscovery = exports.default = exports.anthropicVertexProviderDiscovery = {
  id: PROVIDER_ID,
  label: "Anthropic Vertex",
  docsPath: "/providers/models",
  auth: [],
  catalog: {
    order: "simple",
    run: runAnthropicVertexCatalog
  },
  resolveConfigApiKey: ({ env }) => (0, _regionZm4pn72t.i)(env),
  resolveSyntheticAuth: () => {
    if (!(0, _regionZm4pn72t.t)()) return;
    return {
      apiKey: GCP_VERTEX_CREDENTIALS_MARKER,
      source: "gcp-vertex-credentials (ADC)",
      mode: "api-key"
    };
  }
};
//#endregion /* v9-fd02c269b2ab38ca */
