"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = exports.s = exports.r = exports.o = exports.n = exports.i = exports.a = void 0; //#region extensions/ollama/src/defaults.ts
const OLLAMA_DEFAULT_BASE_URL = exports.n = "http://127.0.0.1:11434";
const OLLAMA_DOCKER_HOST_BASE_URL = exports.s = "http://host.docker.internal:11434";
const OLLAMA_CLOUD_BASE_URL = exports.t = "https://ollama.com";
const OLLAMA_DEFAULT_CONTEXT_WINDOW = exports.r = 128e3;
const OLLAMA_DEFAULT_MAX_TOKENS = exports.a = 8192;
const OLLAMA_DEFAULT_COST = exports.i = {
  input: 0,
  output: 0,
  cacheRead: 0,
  cacheWrite: 0
};
const OLLAMA_DEFAULT_MODEL = exports.o = "gemma4";
//#endregion /* v9-dfb018be893409fd */
