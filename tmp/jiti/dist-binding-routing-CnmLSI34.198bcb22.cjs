"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveConfiguredBindingRoute;exports.r = resolveRuntimeConversationBindingRoute;exports.t = ensureConfiguredBindingRouteReady;var _sessionKeyC0K0uhmG = require("./session-key-C0K0uhmG.js");
var _globalsCZuktVBk = require("./globals-CZuktVBk.js");
var _sessionBindingService7_9X79Yd = require("./session-binding-service-7_9X79Yd.js");
var _resolveRouteBNuWCNW = require("./resolve-route-BNuWCNW8.js");
var _bindingRegistryB8HXLRqx = require("./binding-registry-B8HXLRqx.js");
var _bindingTargetsUoGsDs8V = require("./binding-targets-uoGsDs8V.js");
//#region src/channels/plugins/binding-routing.ts
const CONFIGURED_BINDING_ROUTE_READY_TIMEOUT_MS = 3e4;
function resolveConfiguredBindingConversationRef(params) {
  if ("conversation" in params) return params.conversation;
  return {
    channel: params.channel,
    accountId: params.accountId,
    conversationId: params.conversationId,
    parentConversationId: params.parentConversationId
  };
}
function isPluginOwnedRuntimeBindingRecord(record) {
  const metadata = record?.metadata;
  if (!metadata || typeof metadata !== "object") return false;
  return metadata.pluginBindingOwner === "plugin" && typeof metadata.pluginId === "string" && typeof metadata.pluginRoot === "string";
}
function resolveConfiguredBindingRoute(params) {
  const bindingResolution = (0, _bindingRegistryB8HXLRqx.n)({
    cfg: params.cfg,
    conversation: resolveConfiguredBindingConversationRef(params)
  }) ?? null;
  if (!bindingResolution) return {
    bindingResolution: null,
    route: params.route
  };
  const boundSessionKey = bindingResolution.statefulTarget.sessionKey.trim();
  if (!boundSessionKey) return {
    bindingResolution,
    route: params.route
  };
  const boundAgentId = (0, _sessionKeyC0K0uhmG.u)(boundSessionKey) || bindingResolution.statefulTarget.agentId;
  return {
    bindingResolution,
    boundSessionKey,
    boundAgentId,
    route: {
      ...params.route,
      sessionKey: boundSessionKey,
      agentId: boundAgentId,
      lastRoutePolicy: (0, _resolveRouteBNuWCNW.n)({
        sessionKey: boundSessionKey,
        mainSessionKey: params.route.mainSessionKey
      }),
      matchedBy: "binding.channel"
    }
  };
}
function resolveRuntimeConversationBindingRoute(params) {
  const bindingRecord = (0, _sessionBindingService7_9X79Yd.r)().resolveByConversation(resolveConfiguredBindingConversationRef(params));
  const boundSessionKey = bindingRecord?.targetSessionKey?.trim();
  if (!bindingRecord || !boundSessionKey) return {
    bindingRecord: null,
    route: params.route
  };
  (0, _sessionBindingService7_9X79Yd.r)().touch(bindingRecord.bindingId);
  if (isPluginOwnedRuntimeBindingRecord(bindingRecord)) return {
    bindingRecord,
    route: params.route
  };
  const boundAgentId = (0, _sessionKeyC0K0uhmG.u)(boundSessionKey) || params.route.agentId;
  return {
    bindingRecord,
    boundSessionKey,
    boundAgentId,
    route: {
      ...params.route,
      sessionKey: boundSessionKey,
      agentId: boundAgentId,
      lastRoutePolicy: (0, _resolveRouteBNuWCNW.n)({
        sessionKey: boundSessionKey,
        mainSessionKey: params.route.mainSessionKey
      }),
      matchedBy: "binding.channel"
    }
  };
}
async function ensureConfiguredBindingRouteReady(params) {
  const readyPromise = (0, _bindingTargetsUoGsDs8V.t)(params);
  let timer;
  const timeoutToken = Symbol("configured-binding-route-ready-timeout");
  const timeoutPromise = new Promise((resolve) => {
    timer = setTimeout(() => resolve(timeoutToken), CONFIGURED_BINDING_ROUTE_READY_TIMEOUT_MS);
    timer.unref?.();
  });
  try {
    const result = await Promise.race([readyPromise, timeoutPromise]);
    if (result !== timeoutToken) return result;
    (0, _globalsCZuktVBk.r)(`configured binding route ready check timed out after ${CONFIGURED_BINDING_ROUTE_READY_TIMEOUT_MS / 1e3}s`);
    readyPromise.then((lateResult) => (0, _globalsCZuktVBk.r)(`configured binding route ready check settled after timeout (ok=${lateResult.ok})`), (err) => (0, _globalsCZuktVBk.r)(`configured binding route ready check rejected after timeout: ${String(err)}`));
    return {
      ok: false,
      error: "Configured binding route ready check timed out"
    };
  } finally {
    clearTimeout(timer);
  }
}
//#endregion /* v9-9da1c2166ad61e96 */
