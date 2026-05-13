"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = resolveEffectiveDebugProxyUrl;exports.n = createDebugProxyWebSocketAgent;exports.r = resolveDebugProxySettings;exports.t = applyDebugProxyEnv;var _pathsC1_Y0cDn = require("./paths-C1_Y0cDn.js");
var _nodeProcess = _interopRequireDefault(require("node:process"));
var _nodePath = _interopRequireDefault(require("node:path"));
var _nodeCrypto = require("node:crypto");
var _httpsProxyAgent = require("https-proxy-agent");function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/proxy-capture/paths.ts
function resolveDebugProxyRootDir(env = process.env) {
  return _nodePath.default.join((0, _pathsC1_Y0cDn.v)(env), "debug-proxy");
}
function resolveDebugProxyDbPath(env = process.env) {
  return _nodePath.default.join(resolveDebugProxyRootDir(env), "capture.sqlite");
}
function resolveDebugProxyBlobDir(env = process.env) {
  return _nodePath.default.join(resolveDebugProxyRootDir(env), "blobs");
}
function resolveDebugProxyCertDir(env = process.env) {
  return _nodePath.default.join(resolveDebugProxyRootDir(env), "certs");
}
//#endregion
//#region src/proxy-capture/env.ts
const OPENCLAW_DEBUG_PROXY_ENABLED = "OPENCLAW_DEBUG_PROXY_ENABLED";
const OPENCLAW_DEBUG_PROXY_URL = "OPENCLAW_DEBUG_PROXY_URL";
const OPENCLAW_DEBUG_PROXY_DB_PATH = "OPENCLAW_DEBUG_PROXY_DB_PATH";
const OPENCLAW_DEBUG_PROXY_BLOB_DIR = "OPENCLAW_DEBUG_PROXY_BLOB_DIR";
const OPENCLAW_DEBUG_PROXY_CERT_DIR = "OPENCLAW_DEBUG_PROXY_CERT_DIR";
const OPENCLAW_DEBUG_PROXY_SESSION_ID = "OPENCLAW_DEBUG_PROXY_SESSION_ID";
const OPENCLAW_DEBUG_PROXY_REQUIRE = "OPENCLAW_DEBUG_PROXY_REQUIRE";
let cachedImplicitSessionId;
function isTruthy(value) {
  return value === "1" || value === "true" || value === "yes" || value === "on";
}
function resolveDebugProxySettings(env = _nodeProcess.default.env) {
  const enabled = isTruthy(env[OPENCLAW_DEBUG_PROXY_ENABLED]);
  const sessionId = (env["OPENCLAW_DEBUG_PROXY_SESSION_ID"]?.trim() || void 0) ?? (cachedImplicitSessionId ??= (0, _nodeCrypto.randomUUID)());
  return {
    enabled,
    required: isTruthy(env[OPENCLAW_DEBUG_PROXY_REQUIRE]),
    proxyUrl: env["OPENCLAW_DEBUG_PROXY_URL"]?.trim() || void 0,
    dbPath: env["OPENCLAW_DEBUG_PROXY_DB_PATH"]?.trim() || resolveDebugProxyDbPath(env),
    blobDir: env["OPENCLAW_DEBUG_PROXY_BLOB_DIR"]?.trim() || resolveDebugProxyBlobDir(env),
    certDir: env["OPENCLAW_DEBUG_PROXY_CERT_DIR"]?.trim() || resolveDebugProxyCertDir(env),
    sessionId,
    sourceProcess: "openclaw"
  };
}
function applyDebugProxyEnv(env, params) {
  return {
    ...env,
    [OPENCLAW_DEBUG_PROXY_ENABLED]: "1",
    [OPENCLAW_DEBUG_PROXY_REQUIRE]: "1",
    [OPENCLAW_DEBUG_PROXY_URL]: params.proxyUrl,
    [OPENCLAW_DEBUG_PROXY_DB_PATH]: params.dbPath ?? resolveDebugProxyDbPath(env),
    [OPENCLAW_DEBUG_PROXY_BLOB_DIR]: params.blobDir ?? resolveDebugProxyBlobDir(env),
    [OPENCLAW_DEBUG_PROXY_CERT_DIR]: params.certDir ?? resolveDebugProxyCertDir(env),
    [OPENCLAW_DEBUG_PROXY_SESSION_ID]: params.sessionId,
    HTTP_PROXY: params.proxyUrl,
    HTTPS_PROXY: params.proxyUrl,
    ALL_PROXY: params.proxyUrl
  };
}
function createDebugProxyWebSocketAgent(settings) {
  if (!settings.enabled || !settings.proxyUrl) return;
  return new _httpsProxyAgent.HttpsProxyAgent(settings.proxyUrl);
}
function resolveEffectiveDebugProxyUrl(configuredProxyUrl) {
  const explicit = configuredProxyUrl?.trim();
  if (explicit) return explicit;
  const settings = resolveDebugProxySettings();
  return settings.enabled ? settings.proxyUrl : void 0;
}
//#endregion /* v9-0cdeaee9cf3dd38e */
