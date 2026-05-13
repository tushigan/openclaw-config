"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.complete = complete;exports.completeSimple = completeSimple;Object.defineProperty(exports, "getEnvApiKey", { enumerable: true, get: function () {return _envApiKeys.getEnvApiKey;} });exports.stream = stream;exports.streamSimple = streamSimple;require("./providers/register-builtins.js");
var _apiRegistry = require("./api-registry.js");
var _envApiKeys = require("./env-api-keys.js");
function resolveApiProvider(api) {
  const provider = (0, _apiRegistry.getApiProvider)(api);
  if (!provider) {
    throw new Error(`No API provider registered for api: ${api}`);
  }
  return provider;
}
function stream(model, context, options) {
  const provider = resolveApiProvider(model.api);
  return provider.stream(model, context, options);
}
async function complete(model, context, options) {
  const s = stream(model, context, options);
  return s.result();
}
function streamSimple(model, context, options) {
  const provider = resolveApiProvider(model.api);
  return provider.streamSimple(model, context, options);
}
async function completeSimple(model, context, options) {
  const s = streamSimple(model, context, options);
  return s.result();
} /* v9-2164a82acd37ffad */
