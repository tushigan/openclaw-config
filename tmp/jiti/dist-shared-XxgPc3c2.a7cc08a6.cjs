"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = postJsonRequest;exports.c = requireTranscriptionText;exports.d = resolveProviderOperationTimeoutMs;exports.f = waitProviderOperationPollInterval;exports.i = pollProviderOperationJson;exports.l = resolveAudioTranscriptionUploadFileName;exports.n = createProviderOperationDeadline;exports.o = postMultipartRequest;exports.r = fetchWithTimeoutGuarded;exports.s = postTranscriptionRequest;exports.t = buildAudioTranscriptionFormData;exports.u = resolveProviderHttpRequestConfig;var _proxyEnvBaS80pvI = require("./proxy-env-BaS80pvI.js");
var _providerRequestConfigBfgay7t = require("./provider-request-config-Bfgay7t4.js");
var _fetchTimeoutBJUkaK0F = require("./fetch-timeout-BJUkaK0F.js");
var _fetchGuardDFNmfAZx = require("./fetch-guard-DFNmfAZx.js");
var _providerHttpErrorsD1NPNIxO = require("./provider-http-errors-D1NPNIxO.js");
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/media-understanding/shared.ts
const DEFAULT_GUARDED_HTTP_TIMEOUT_MS = 6e4;
const MAX_AUDIT_CONTEXT_CHARS = 80;
function resolveAudioTranscriptionUploadFileName(fileName, mime) {
  const trimmed = fileName?.trim();
  const baseName = trimmed ? _nodePath.default.basename(trimmed) : "audio";
  const lowerMime = mime?.trim().toLowerCase();
  if (/\.aac$/i.test(baseName)) return `${baseName.slice(0, -4) || "audio"}.m4a`;
  if (!_nodePath.default.extname(baseName) && lowerMime === "audio/aac") return `${baseName || "audio"}.m4a`;
  return baseName;
}
function buildAudioTranscriptionFormData(params) {
  const form = new FormData();
  const bytes = new Uint8Array(params.buffer);
  const blob = new Blob([bytes], { type: params.mime ?? "application/octet-stream" });
  form.append("file", blob, resolveAudioTranscriptionUploadFileName(params.fileName, params.mime));
  for (const [name, value] of Object.entries(params.fields ?? {})) {
    const text = typeof value === "string" ? value.trim() : value == null ? "" : String(value);
    if (text) form.append(name, text);
  }
  return form;
}
function createProviderOperationDeadline(params) {
  if (typeof params.timeoutMs !== "number" || !Number.isFinite(params.timeoutMs) || params.timeoutMs <= 0) return { label: params.label };
  const timeoutMs = Math.floor(params.timeoutMs);
  return {
    deadlineAtMs: Date.now() + timeoutMs,
    label: params.label,
    timeoutMs
  };
}
function resolveProviderOperationTimeoutMs(params) {
  const deadlineAtMs = params.deadline.deadlineAtMs;
  if (typeof deadlineAtMs !== "number") return params.defaultTimeoutMs;
  const remainingMs = deadlineAtMs - Date.now();
  if (remainingMs <= 0) throw new Error(`${params.deadline.label} timed out after ${params.deadline.timeoutMs}ms`);
  return Math.max(1, Math.min(params.defaultTimeoutMs, remainingMs));
}
async function waitProviderOperationPollInterval(params) {
  const deadlineAtMs = params.deadline.deadlineAtMs;
  if (typeof deadlineAtMs !== "number") {
    await new Promise((resolve) => setTimeout(resolve, params.pollIntervalMs));
    return;
  }
  const remainingMs = deadlineAtMs - Date.now();
  if (remainingMs <= 0) throw new Error(`${params.deadline.label} timed out after ${params.deadline.timeoutMs}ms`);
  await new Promise((resolve) => setTimeout(resolve, Math.min(params.pollIntervalMs, remainingMs)));
}
async function pollProviderOperationJson(params) {
  for (let attempt = 0; attempt < params.maxAttempts; attempt += 1) {
    const response = await (0, _fetchTimeoutBJUkaK0F.r)(params.url, {
      method: "GET",
      headers: params.headers
    }, resolveProviderOperationTimeoutMs({
      deadline: params.deadline,
      defaultTimeoutMs: params.defaultTimeoutMs
    }), params.fetchFn);
    await (0, _providerHttpErrorsD1NPNIxO.r)(response, params.requestFailedMessage);
    const payload = await response.json();
    if (params.isComplete(payload)) return payload;
    const failureMessage = params.getFailureMessage?.(payload);
    if (failureMessage) throw new Error(failureMessage);
    await waitProviderOperationPollInterval({
      deadline: params.deadline,
      pollIntervalMs: params.pollIntervalMs
    });
  }
  throw new Error(params.timeoutMessage);
}
function resolveGuardedHttpTimeoutMs(timeoutMs) {
  if (typeof timeoutMs !== "number" || !Number.isFinite(timeoutMs) || timeoutMs <= 0) return DEFAULT_GUARDED_HTTP_TIMEOUT_MS;
  return timeoutMs;
}
function sanitizeAuditContext(auditContext) {
  const cleaned = auditContext?.replace(/\p{Cc}+/gu, " ").replace(/\s+/g, " ").trim();
  if (!cleaned) return;
  return cleaned.slice(0, MAX_AUDIT_CONTEXT_CHARS);
}
function resolveProviderHttpRequestConfig(params) {
  const requestConfig = (0, _providerRequestConfigBfgay7t.l)({
    provider: params.provider ?? "",
    baseUrl: params.baseUrl,
    defaultBaseUrl: params.defaultBaseUrl,
    capability: params.capability ?? "other",
    transport: params.transport ?? "http",
    callerHeaders: params.headers ? Object.fromEntries(new Headers(params.headers).entries()) : void 0,
    providerHeaders: params.defaultHeaders,
    precedence: "caller-wins",
    allowPrivateNetwork: params.allowPrivateNetwork,
    api: params.api,
    request: params.request
  });
  const headers = new Headers(requestConfig.headers);
  if (!requestConfig.baseUrl) throw new Error("Missing baseUrl: provide baseUrl or defaultBaseUrl");
  return {
    baseUrl: requestConfig.baseUrl,
    allowPrivateNetwork: requestConfig.allowPrivateNetwork,
    headers,
    dispatcherPolicy: (0, _providerRequestConfigBfgay7t.n)(requestConfig),
    requestConfig
  };
}
/**
* Decide whether to auto-upgrade a provider HTTP request into
* `TRUSTED_ENV_PROXY` mode based on the runtime environment.
*
* This is gated conservatively to avoid the SSRF bypasses the initial
* auto-upgrade path exposed (see openclaw#64974 review threads):
*
* 1. If the caller supplied an explicit `dispatcherPolicy` — custom proxy URL,
*    `proxyTls`, or `connect` options — do NOT override it. Trusted-env mode
*    builds an `EnvHttpProxyAgent` that would silently drop those overrides,
*    breaking enterprise proxy/mTLS configs.
*
* 2. Only auto-upgrade when `HTTP_PROXY` or `HTTPS_PROXY` (lower- or
*    upper-case) is configured for the target protocol. `ALL_PROXY` is
*    explicitly ignored by `EnvHttpProxyAgent`, so counting it would
*    auto-upgrade requests that then make direct connections while skipping
*    pinned-DNS/SSRF hostname checks.
*
* 3. If `NO_PROXY` would bypass the proxy for this target, do NOT auto-upgrade.
*    `EnvHttpProxyAgent` makes direct connections for `NO_PROXY` matches, but
*    in `TRUSTED_ENV_PROXY` mode `fetchWithSsrFGuard` skips
*    `resolvePinnedHostnameWithPolicy` — so those direct connections would
*    bypass SSRF protection. Keep strict mode for `NO_PROXY` matches.
*/
function shouldAutoUpgradeToTrustedEnvProxy(params) {
  if (params.dispatcherPolicy) return false;
  return (0, _proxyEnvBaS80pvI.c)(params.url);
}
async function fetchWithTimeoutGuarded(url, init, timeoutMs, fetchFn, options) {
  const resolvedMode = options?.mode ?? (shouldAutoUpgradeToTrustedEnvProxy({
    url,
    dispatcherPolicy: options?.dispatcherPolicy
  }) ? _fetchGuardDFNmfAZx.t.TRUSTED_ENV_PROXY : void 0);
  return await (0, _fetchGuardDFNmfAZx.n)({
    url,
    fetchImpl: fetchFn,
    init,
    timeoutMs: resolveGuardedHttpTimeoutMs(timeoutMs),
    policy: options?.ssrfPolicy,
    lookupFn: options?.lookupFn,
    pinDns: options?.pinDns,
    dispatcherPolicy: options?.dispatcherPolicy,
    auditContext: sanitizeAuditContext(options?.auditContext),
    ...(resolvedMode ? { mode: resolvedMode } : {})
  });
}
function resolveGuardedPostRequestOptions(params) {
  if (!params.allowPrivateNetwork && !params.dispatcherPolicy && params.pinDns === void 0 && !params.auditContext && params.mode === void 0) return;
  return {
    ...(params.allowPrivateNetwork ? { ssrfPolicy: { allowPrivateNetwork: true } } : {}),
    ...(params.pinDns !== void 0 ? { pinDns: params.pinDns } : {}),
    ...(params.dispatcherPolicy ? { dispatcherPolicy: params.dispatcherPolicy } : {}),
    ...(params.auditContext ? { auditContext: params.auditContext } : {}),
    ...(params.mode !== void 0 ? { mode: params.mode } : {})
  };
}
async function postTranscriptionRequest(params) {
  return fetchWithTimeoutGuarded(params.url, {
    method: "POST",
    headers: params.headers,
    body: params.body
  }, params.timeoutMs, params.fetchFn, resolveGuardedPostRequestOptions(params));
}
async function postJsonRequest(params) {
  return fetchWithTimeoutGuarded(params.url, {
    method: "POST",
    headers: params.headers,
    body: JSON.stringify(params.body)
  }, params.timeoutMs, params.fetchFn, resolveGuardedPostRequestOptions(params));
}
async function postMultipartRequest(params) {
  return fetchWithTimeoutGuarded(params.url, {
    method: "POST",
    headers: params.headers,
    body: params.body
  }, params.timeoutMs, params.fetchFn, resolveGuardedPostRequestOptions(params));
}
function requireTranscriptionText(value, missingMessage) {
  const text = value?.trim();
  if (!text) throw new Error(missingMessage);
  return text;
}
//#endregion /* v9-c40622542151e9ec */
