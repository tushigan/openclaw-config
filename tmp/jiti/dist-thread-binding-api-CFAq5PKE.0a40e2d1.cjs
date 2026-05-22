"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveBundledChannelThreadBindingInboundConversation;exports.t = resolveBundledChannelThreadBindingDefaultPlacement;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _publicSurfaceLoaderDAC6GNWm = require("./public-surface-loader-DAC6GNWm.js");
//#region src/channels/plugins/thread-binding-api.ts
const THREAD_BINDING_API_ARTIFACT_BASENAME = "thread-binding-api.js";
const MISSING_PUBLIC_SURFACE_PREFIX = "Unable to resolve bundled plugin public surface ";
function loadBundledChannelThreadBindingApi(channelId) {
  const cacheKey = channelId.trim();
  try {
    return (0, _publicSurfaceLoaderDAC6GNWm.t)({
      dirName: cacheKey,
      artifactBasename: THREAD_BINDING_API_ARTIFACT_BASENAME
    });
  } catch (error) {
    if (error instanceof Error && error.message.startsWith(MISSING_PUBLIC_SURFACE_PREFIX)) return;
    throw error;
  }
}
function normalizeThreadBindingPlacement(value) {
  const normalized = (0, _stringCoerceBje8XVt.c)(typeof value === "string" ? value : void 0);
  return normalized === "current" || normalized === "child" ? normalized : void 0;
}
function resolveBundledChannelThreadBindingDefaultPlacement(channelId) {
  return normalizeThreadBindingPlacement(loadBundledChannelThreadBindingApi(channelId)?.defaultTopLevelPlacement);
}
function resolveBundledChannelThreadBindingInboundConversation(params) {
  const api = loadBundledChannelThreadBindingApi(params.channelId);
  if (typeof api?.resolveInboundConversation !== "function") return;
  return api.resolveInboundConversation({
    from: params.from,
    to: params.to,
    conversationId: params.conversationId,
    threadId: params.threadId,
    isGroup: params.isGroup
  });
}
//#endregion /* v9-1b64c4ed0cbf11a4 */
