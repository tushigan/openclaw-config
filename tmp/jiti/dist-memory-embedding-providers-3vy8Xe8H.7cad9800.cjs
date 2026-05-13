"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = listRegisteredMemoryEmbeddingProviders;exports.i = listMemoryEmbeddingProviders;exports.n = getMemoryEmbeddingProvider;exports.o = registerMemoryEmbeddingProvider;exports.r = getRegisteredMemoryEmbeddingProvider;exports.s = restoreRegisteredMemoryEmbeddingProviders;exports.t = clearMemoryEmbeddingProviders; //#region src/plugins/memory-embedding-providers.ts
const MEMORY_EMBEDDING_PROVIDERS_KEY = Symbol.for("openclaw.memoryEmbeddingProviders");
function getMemoryEmbeddingProviders() {
  const globalStore = globalThis;
  const existing = globalStore[MEMORY_EMBEDDING_PROVIDERS_KEY];
  if (existing instanceof Map) return existing;
  const created = /* @__PURE__ */new Map();
  globalStore[MEMORY_EMBEDDING_PROVIDERS_KEY] = created;
  return created;
}
function registerMemoryEmbeddingProvider(adapter, options) {
  getMemoryEmbeddingProviders().set(adapter.id, {
    adapter,
    ownerPluginId: options?.ownerPluginId
  });
}
function getRegisteredMemoryEmbeddingProvider(id) {
  return getMemoryEmbeddingProviders().get(id);
}
function getMemoryEmbeddingProvider(id) {
  return getMemoryEmbeddingProviders().get(id)?.adapter;
}
function listRegisteredMemoryEmbeddingProviders() {
  return Array.from(getMemoryEmbeddingProviders().values());
}
function listMemoryEmbeddingProviders() {
  return listRegisteredMemoryEmbeddingProviders().map((entry) => entry.adapter);
}
function restoreRegisteredMemoryEmbeddingProviders(entries) {
  getMemoryEmbeddingProviders().clear();
  for (const entry of entries) registerMemoryEmbeddingProvider(entry.adapter, { ownerPluginId: entry.ownerPluginId });
}
function clearMemoryEmbeddingProviders() {
  getMemoryEmbeddingProviders().clear();
}
//#endregion /* v9-aef30aff79d2f1ff */
