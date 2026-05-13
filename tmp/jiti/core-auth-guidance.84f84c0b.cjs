"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.formatNoApiKeyFoundMessage = formatNoApiKeyFoundMessage;exports.formatNoModelSelectedMessage = formatNoModelSelectedMessage;exports.formatNoModelsAvailableMessage = formatNoModelsAvailableMessage;exports.getProviderLoginHelp = getProviderLoginHelp;var _nodePath = require("node:path");
var _config = require("../config.js");
const UNKNOWN_PROVIDER = "unknown";
function getProviderLoginHelp() {
  return [
  "Use /login to log into a provider via OAuth or API key. See:",
  `  ${(0, _nodePath.join)((0, _config.getDocsPath)(), "providers.md")}`,
  `  ${(0, _nodePath.join)((0, _config.getDocsPath)(), "models.md")}`].
  join("\n");
}
function formatNoModelsAvailableMessage() {
  return `No models available. ${getProviderLoginHelp()}`;
}
function formatNoModelSelectedMessage() {
  return `No model selected.\n\n${getProviderLoginHelp()}\n\nThen use /model to select a model.`;
}
function formatNoApiKeyFoundMessage(provider) {
  const providerDisplay = provider === UNKNOWN_PROVIDER ? "the selected model" : provider;
  return `No API key found for ${providerDisplay}.\n\n${getProviderLoginHelp()}`;
} /* v9-b3f5224a26d6668f */
