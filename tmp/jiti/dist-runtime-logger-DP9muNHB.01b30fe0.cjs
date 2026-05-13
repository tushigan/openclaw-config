"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveRuntimeEnv;exports.r = resolveRuntimeEnvWithUnavailableExit;exports.t = createLoggerBackedRuntime;var _nodeUtil = require("node:util");
//#region src/plugin-sdk/runtime-logger.ts
/** Adapt a simple logger into the RuntimeEnv contract used by shared plugin SDK helpers. */
function createLoggerBackedRuntime(params) {
  return {
    log: (...args) => {
      params.logger.info((0, _nodeUtil.format)(...args));
    },
    error: (...args) => {
      params.logger.error((0, _nodeUtil.format)(...args));
    },
    writeStdout: (value) => {
      params.logger.info(value);
    },
    writeJson: (value, space = 2) => {
      params.logger.info(JSON.stringify(value, null, space > 0 ? space : void 0));
    },
    exit: (code) => {
      throw params.exitError?.(code) ?? /* @__PURE__ */new Error(`exit ${code}`);
    }
  };
}
function resolveRuntimeEnv(params) {
  return params.runtime ?? createLoggerBackedRuntime(params);
}
function resolveRuntimeEnvWithUnavailableExit(params) {
  if (params.runtime) return resolveRuntimeEnv({
    runtime: params.runtime,
    logger: params.logger,
    exitError: () => new Error(params.unavailableMessage ?? "Runtime exit not available")
  });
  return resolveRuntimeEnv({
    logger: params.logger,
    exitError: () => new Error(params.unavailableMessage ?? "Runtime exit not available")
  });
}
//#endregion /* v9-111a9abc4c9ad69f */
