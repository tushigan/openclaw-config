"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = withPluginRuntimeGatewayRequestScope;exports.r = withPluginRuntimePluginIdScope;exports.t = getPluginRuntimeGatewayRequestScope;var _globalSingletonDZyLAEQq = require("./global-singleton-DZyLAEQq.js");
var _nodeAsync_hooks = require("node:async_hooks");
//#region src/plugins/runtime/gateway-request-scope.ts
const pluginRuntimeGatewayRequestScope = (0, _globalSingletonDZyLAEQq.n)(Symbol.for("openclaw.pluginRuntimeGatewayRequestScope"), () => new _nodeAsync_hooks.AsyncLocalStorage());
/**
* Runs plugin gateway handlers with request-scoped context that runtime helpers can read.
*/
function withPluginRuntimeGatewayRequestScope(scope, run) {
  return pluginRuntimeGatewayRequestScope.run(scope, run);
}
/**
* Runs work under the current gateway request scope while attaching plugin identity.
*/
function withPluginRuntimePluginIdScope(pluginId, run) {
  const current = pluginRuntimeGatewayRequestScope.getStore();
  const scoped = current ? {
    ...current,
    pluginId
  } : {
    pluginId,
    isWebchatConnect: () => false
  };
  return pluginRuntimeGatewayRequestScope.run(scoped, run);
}
/**
* Returns the current plugin gateway request scope when called from a plugin request handler.
*/
function getPluginRuntimeGatewayRequestScope() {
  return pluginRuntimeGatewayRequestScope.getStore();
}
//#endregion /* v9-7fc45d65e634e8aa */
