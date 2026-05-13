"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = coerceStatusIssueAccountId;exports.c = mapPluginConfigIssues;exports.d = readStatusIssueFields;exports.f = requireChannelOpenAllowFrom;exports.h = runStoppablePassiveMonitor;exports.i = canResolveEnvSecretRefInReadOnlyPath;exports.l = normalizePluginConfigIssuePath;exports.m = resolveLoggerBackedRuntime;exports.n = buildPassiveProbedChannelStatusSummary;exports.o = createDeferred;exports.p = resolveAmbientNodeProxyAgent;exports.r = buildTrafficStatusSummary;exports.s = formatPluginConfigIssue;exports.t = buildPassiveChannelStatusSummary;exports.u = readPluginPackageVersion;var _refContractFVeYRZYq = require("./ref-contract-FVeYRZYq.js");
var _proxyEnvBaS80pvI = require("./proxy-env-BaS80pvI.js");
require("./fetch-timeout-BJUkaK0F.js");
var _channelLifecycleCoreBcJ10WSB = require("./channel-lifecycle.core-BcJ10WSB.js");
var _runtimeLoggerDP9muNHB = require("./runtime-logger-DP9muNHB.js");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}
//#region src/plugin-sdk/extension-shared.ts
function buildPassiveChannelStatusSummary(snapshot, extra) {
  return {
    configured: snapshot.configured ?? false,
    ...(extra ?? {}),
    running: snapshot.running ?? false,
    lastStartAt: snapshot.lastStartAt ?? null,
    lastStopAt: snapshot.lastStopAt ?? null,
    lastError: snapshot.lastError ?? null
  };
}
function buildPassiveProbedChannelStatusSummary(snapshot, extra) {
  return {
    ...buildPassiveChannelStatusSummary(snapshot, extra),
    probe: snapshot.probe,
    lastProbeAt: snapshot.lastProbeAt ?? null
  };
}
function buildTrafficStatusSummary(snapshot) {
  return {
    lastInboundAt: snapshot?.lastInboundAt ?? null,
    lastOutboundAt: snapshot?.lastOutboundAt ?? null
  };
}
async function runStoppablePassiveMonitor(params) {
  await (0, _channelLifecycleCoreBcJ10WSB.i)({
    abortSignal: params.abortSignal,
    start: params.start,
    stop: async (monitor) => {
      monitor.stop();
    }
  });
}
function resolveLoggerBackedRuntime(runtime, logger) {
  return runtime ?? (0, _runtimeLoggerDP9muNHB.t)({
    logger,
    exitError: () => /* @__PURE__ */new Error("Runtime exit not available")
  });
}
function requireChannelOpenAllowFrom(params) {
  params.requireOpenAllowFrom({
    policy: params.policy,
    allowFrom: params.allowFrom,
    ctx: params.ctx,
    path: ["allowFrom"],
    message: `channels.${params.channel}.dmPolicy="open" requires channels.${params.channel}.allowFrom to include "*"`
  });
}
function readStatusIssueFields(value, fields) {
  if (!value || typeof value !== "object") return null;
  const record = value;
  const result = {};
  for (const field of fields) result[field] = record[field];
  return result;
}
function coerceStatusIssueAccountId(value) {
  return typeof value === "string" ? value : typeof value === "number" ? String(value) : void 0;
}
function createDeferred() {
  let resolve;
  let reject;
  return {
    promise: new Promise((res, rej) => {
      resolve = res;
      reject = rej;
    }),
    resolve,
    reject
  };
}
const DEFAULT_PACKAGE_JSON_VERSION_CANDIDATES = [
"../package.json",
"./package.json",
"../../package.json"];

function formatPluginConfigIssue(issue, options) {
  if (!issue) return options?.invalidConfigMessage ?? "invalid config";
  if (issue.code === "unrecognized_keys" && issue.keys.length > 0) return options?.unknownKeyMessage?.(issue.keys[0]) ?? `unknown config key: ${issue.keys[0]}`;
  if (issue.code === "invalid_type" && issue.path.length === 0) return options?.rootInvalidTypeMessage ?? "expected config object";
  return issue.message;
}
function normalizePluginConfigIssuePath(path) {
  return path.filter((segment) => {
    const kind = typeof segment;
    return kind === "string" || kind === "number";
  });
}
function mapPluginConfigIssues(issues, options) {
  return issues.map((issue) => ({
    path: normalizePluginConfigIssuePath(issue.path),
    message: formatPluginConfigIssue(issue, options)
  }));
}
function canResolveEnvSecretRefInReadOnlyPath(params) {
  const providerConfig = params.cfg?.secrets?.providers?.[params.provider];
  if (!providerConfig) return params.provider === (0, _refContractFVeYRZYq.l)(params.cfg ?? {}, "env");
  if (providerConfig.source !== "env") return false;
  const allowlist = providerConfig.allowlist;
  return !allowlist || allowlist.includes(params.id);
}
function readPluginPackageVersion(params) {
  for (const candidate of params.candidates ?? DEFAULT_PACKAGE_JSON_VERSION_CANDIDATES) try {
    const version = params.require(candidate).version;
    if (typeof version === "string" && version.trim().length > 0) return version;
  } catch {}
  return params.fallback ?? "unknown";
}
let proxyAgentConstructorPromise = null;
async function loadProxyAgentConstructor() {
  proxyAgentConstructorPromise ??= Promise.resolve().then(() => jitiImport("proxy-agent").then((m) => _interopRequireWildcard(m))).then(({ ProxyAgent }) => ProxyAgent);
  return proxyAgentConstructorPromise;
}
async function resolveAmbientNodeProxyAgent(params) {
  if (!(0, _proxyEnvBaS80pvI.r)(params?.protocol ?? "https")) return;
  try {
    const ProxyAgent = await loadProxyAgentConstructor();
    params?.onUsingProxy?.();
    return new ProxyAgent();
  } catch (error) {
    params?.onError?.(error);
    return;
  }
}
//#endregion /* v9-7ae694c319844cad */
