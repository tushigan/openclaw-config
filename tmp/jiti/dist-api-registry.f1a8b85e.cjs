"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.clearApiProviders = clearApiProviders;exports.getApiProvider = getApiProvider;exports.getApiProviders = getApiProviders;exports.registerApiProvider = registerApiProvider;exports.unregisterApiProviders = unregisterApiProviders;const apiProviderRegistry = new Map();
function wrapStream(api, stream) {
  return (model, context, options) => {
    if (model.api !== api) {
      throw new Error(`Mismatched api: ${model.api} expected ${api}`);
    }
    return stream(model, context, options);
  };
}
function wrapStreamSimple(api, streamSimple) {
  return (model, context, options) => {
    if (model.api !== api) {
      throw new Error(`Mismatched api: ${model.api} expected ${api}`);
    }
    return streamSimple(model, context, options);
  };
}
function registerApiProvider(provider, sourceId) {
  apiProviderRegistry.set(provider.api, {
    provider: {
      api: provider.api,
      stream: wrapStream(provider.api, provider.stream),
      streamSimple: wrapStreamSimple(provider.api, provider.streamSimple)
    },
    sourceId
  });
}
function getApiProvider(api) {
  return apiProviderRegistry.get(api)?.provider;
}
function getApiProviders() {
  return Array.from(apiProviderRegistry.values(), (entry) => entry.provider);
}
function unregisterApiProviders(sourceId) {
  for (const [api, entry] of apiProviderRegistry.entries()) {
    if (entry.sourceId === sourceId) {
      apiProviderRegistry.delete(api);
    }
  }
}
function clearApiProviders() {
  apiProviderRegistry.clear();
} /* v9-99da5677229ee407 */
