"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = resolvePluginRuntimeLoadContext;exports.n = buildPluginRuntimeLoadOptionsFromValues;exports.r = createPluginRuntimeLoaderLogger;exports.t = buildPluginRuntimeLoadOptions;var _agentScopeB6RIBoEj = require("./agent-scope-B6RIBoEj.js");
var _subsystemCxWoQXRD = require("./subsystem-CxWoQXRD.js");
var _ioE69J4lLI = require("./io-E69J4lLI.js");
require("./config-Dq84uU6c.js");
var _pluginAutoEnableBNUgpUnK = require("./plugin-auto-enable-BNUgpUnK.js");
var _loaderBGXgDrk = require("./loader-B-GXgDrk.js");
require("./logging-DZKzaN8o.js");
//#region src/plugins/runtime/load-context.ts
const log = (0, _subsystemCxWoQXRD.t)("plugins");
function createPluginRuntimeLoaderLogger() {
  return {
    info: (message) => log.info(message),
    warn: (message) => log.warn(message),
    error: (message) => log.error(message),
    debug: (message) => log.debug(message)
  };
}
function resolvePluginRuntimeLoadContext(options) {
  const env = options?.env ?? process.env;
  const rawConfig = options?.config ?? (0, _ioE69J4lLI.i)();
  const activationSourceConfig = (0, _loaderBGXgDrk.x)({
    config: rawConfig,
    activationSourceConfig: options?.activationSourceConfig
  });
  const autoEnabled = (0, _pluginAutoEnableBNUgpUnK.t)({
    config: rawConfig,
    env,
    manifestRegistry: options?.manifestRegistry
  });
  const config = autoEnabled.config;
  const workspaceDir = options?.workspaceDir ?? (0, _agentScopeB6RIBoEj.x)(config, (0, _agentScopeB6RIBoEj.S)(config));
  return {
    rawConfig,
    config,
    activationSourceConfig,
    autoEnabledReasons: autoEnabled.autoEnabledReasons,
    workspaceDir,
    env,
    logger: options?.logger ?? createPluginRuntimeLoaderLogger()
  };
}
function buildPluginRuntimeLoadOptions(context, overrides) {
  return buildPluginRuntimeLoadOptionsFromValues(context, overrides);
}
function buildPluginRuntimeLoadOptionsFromValues(values, overrides) {
  return {
    config: values.config,
    activationSourceConfig: values.activationSourceConfig,
    autoEnabledReasons: values.autoEnabledReasons,
    workspaceDir: values.workspaceDir,
    env: values.env,
    logger: values.logger,
    ...overrides
  };
}
//#endregion /* v9-64acd91177ccf4d5 */
