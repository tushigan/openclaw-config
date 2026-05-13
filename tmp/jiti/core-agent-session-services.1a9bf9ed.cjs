"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.createAgentSessionFromServices = createAgentSessionFromServices;exports.createAgentSessionServices = createAgentSessionServices;var _nodePath = require("node:path");
var _config = require("../config.js");
var _authStorage = require("./auth-storage.js");
var _modelRegistry = require("./model-registry.js");
var _resourceLoader = require("./resource-loader.js");
var _sdk = require("./sdk.js");
var _settingsManager = require("./settings-manager.js");
function applyExtensionFlagValues(resourceLoader, extensionFlagValues) {
  if (!extensionFlagValues) {
    return [];
  }
  const diagnostics = [];
  const extensionsResult = resourceLoader.getExtensions();
  const registeredFlags = new Map();
  for (const extension of extensionsResult.extensions) {
    for (const [name, flag] of extension.flags) {
      registeredFlags.set(name, { type: flag.type });
    }
  }
  const unknownFlags = [];
  for (const [name, value] of extensionFlagValues) {
    const flag = registeredFlags.get(name);
    if (!flag) {
      unknownFlags.push(name);
      continue;
    }
    if (flag.type === "boolean") {
      extensionsResult.runtime.flagValues.set(name, true);
      continue;
    }
    if (typeof value === "string") {
      extensionsResult.runtime.flagValues.set(name, value);
      continue;
    }
    diagnostics.push({
      type: "error",
      message: `Extension flag "--${name}" requires a value`
    });
  }
  if (unknownFlags.length > 0) {
    diagnostics.push({
      type: "error",
      message: `Unknown option${unknownFlags.length === 1 ? "" : "s"}: ${unknownFlags.map((name) => `--${name}`).join(", ")}`
    });
  }
  return diagnostics;
}
/**
 * Create cwd-bound runtime services.
 *
 * Returns services plus diagnostics. It does not create an AgentSession.
 */
async function createAgentSessionServices(options) {
  const cwd = options.cwd;
  const agentDir = options.agentDir ?? (0, _config.getAgentDir)();
  const authStorage = options.authStorage ?? _authStorage.AuthStorage.create((0, _nodePath.join)(agentDir, "auth.json"));
  const settingsManager = options.settingsManager ?? _settingsManager.SettingsManager.create(cwd, agentDir);
  const modelRegistry = options.modelRegistry ?? _modelRegistry.ModelRegistry.create(authStorage, (0, _nodePath.join)(agentDir, "models.json"));
  const resourceLoader = new _resourceLoader.DefaultResourceLoader({
    ...(options.resourceLoaderOptions ?? {}),
    cwd,
    agentDir,
    settingsManager
  });
  await resourceLoader.reload();
  const diagnostics = [];
  const extensionsResult = resourceLoader.getExtensions();
  for (const { name, config, extensionPath } of extensionsResult.runtime.pendingProviderRegistrations) {
    try {
      modelRegistry.registerProvider(name, config);
    }
    catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      diagnostics.push({
        type: "error",
        message: `Extension "${extensionPath}" error: ${message}`
      });
    }
  }
  extensionsResult.runtime.pendingProviderRegistrations = [];
  diagnostics.push(...applyExtensionFlagValues(resourceLoader, options.extensionFlagValues));
  return {
    cwd,
    agentDir,
    authStorage,
    settingsManager,
    modelRegistry,
    resourceLoader,
    diagnostics
  };
}
/**
 * Create an AgentSession from previously created services.
 *
 * This keeps session creation separate from service creation so callers can
 * resolve model, thinking, tools, and other session inputs against the target
 * cwd before constructing the session.
 */
async function createAgentSessionFromServices(options) {
  return (0, _sdk.createAgentSession)({
    cwd: options.services.cwd,
    agentDir: options.services.agentDir,
    authStorage: options.services.authStorage,
    settingsManager: options.services.settingsManager,
    modelRegistry: options.services.modelRegistry,
    resourceLoader: options.services.resourceLoader,
    sessionManager: options.sessionManager,
    model: options.model,
    thinkingLevel: options.thinkingLevel,
    scopedModels: options.scopedModels,
    tools: options.tools,
    noTools: options.noTools,
    customTools: options.customTools,
    sessionStartEvent: options.sessionStartEvent
  });
} /* v9-8c2170a5dcd96464 */
