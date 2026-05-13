"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = withTrustedEnvProxyGuardedFetchMode;exports.i = withStrictGuardedFetchMode;exports.n = fetchWithSsrFGuard;exports.o = withTrustedExplicitProxyGuardedFetchMode;exports.r = retainSafeHeadersForCrossOriginRedirectHeaders;exports.t = void 0;var _loggerDksTYIAF = require("./logger-DksTYIAF.js");
var _proxyEnvBaS80pvI = require("./proxy-env-BaS80pvI.js");
var _undiciGlobalDispatcherBb3wFVad = require("./undici-global-dispatcher-Bb3wFVad.js");
var _fetchHeadersDrgi2oEU = require("./fetch-headers-Drgi2oEU.js");
var _runtimeCHdWdufZ = require("./runtime-CHdWdufZ.js");
var _fetchTimeoutBJUkaK0F = require("./fetch-timeout-BJUkaK0F.js");
var _redirectHeadersCdvG9Jv = require("./redirect-headers-CdvG9Jv0.js");
var _undiciRuntimeBdHHFzbs = require("./undici-runtime-BdHHFzbs.js");
var _runtimeFetchD8j2J4DT = require("./runtime-fetch-D8j2J4DT.js");
var _ssrfB5bGsnx = require("./ssrf-B5bGsnx-.js");
//#region src/infra/net/fetch-guard.ts
function resolveDispatcherTimeoutMs(fromParams) {
  if (fromParams !== void 0) return fromParams;
  if (_undiciGlobalDispatcherBb3wFVad.n !== void 0) return _undiciGlobalDispatcherBb3wFVad.n;
}
const GUARDED_FETCH_MODE = exports.t = {
  STRICT: "strict",
  TRUSTED_ENV_PROXY: "trusted_env_proxy",
  TRUSTED_EXPLICIT_PROXY: "trusted_explicit_proxy"
};
const DEFAULT_MAX_REDIRECTS = 3;
function withStrictGuardedFetchMode(params) {
  return {
    ...params,
    mode: GUARDED_FETCH_MODE.STRICT
  };
}
function withTrustedEnvProxyGuardedFetchMode(params) {
  return {
    ...params,
    mode: GUARDED_FETCH_MODE.TRUSTED_ENV_PROXY
  };
}
function withTrustedExplicitProxyGuardedFetchMode(params) {
  return {
    ...params,
    mode: GUARDED_FETCH_MODE.TRUSTED_EXPLICIT_PROXY
  };
}
function resolveGuardedFetchMode(params) {
  if (params.mode) return params.mode;
  if (params.proxy === "env" && params.dangerouslyAllowEnvProxyWithoutPinnedDns === true) return GUARDED_FETCH_MODE.TRUSTED_ENV_PROXY;
  return GUARDED_FETCH_MODE.STRICT;
}
function isManagedProxyActive() {
  return process.env["OPENCLAW_PROXY_ACTIVE"] === "1";
}
function assertExplicitProxySupportsPinnedDns(url, dispatcherPolicy, pinDns) {
  if (pinDns !== false && dispatcherPolicy?.mode === "explicit-proxy" && url.protocol !== "https:") throw new Error("Explicit proxy SSRF pinning requires HTTPS targets; plain HTTP targets are not supported");
}
function createPolicyDispatcherWithoutPinnedDns(dispatcherPolicy, timeoutMs) {
  if (!dispatcherPolicy) return null;
  if (dispatcherPolicy.mode === "direct") return (0, _undiciRuntimeBdHHFzbs.t)(dispatcherPolicy.connect ? { connect: { ...dispatcherPolicy.connect } } : void 0, timeoutMs);
  if (dispatcherPolicy.mode === "env-proxy") return (0, _undiciRuntimeBdHHFzbs.n)({
    ...(dispatcherPolicy.connect ? { connect: { ...dispatcherPolicy.connect } } : {}),
    ...(dispatcherPolicy.proxyTls ? { proxyTls: { ...dispatcherPolicy.proxyTls } } : {})
  }, timeoutMs);
  const proxyUrl = dispatcherPolicy.proxyUrl.trim();
  if (dispatcherPolicy.proxyTls) return (0, _undiciRuntimeBdHHFzbs.r)({
    uri: proxyUrl,
    requestTls: { ...dispatcherPolicy.proxyTls }
  }, timeoutMs);
  return (0, _undiciRuntimeBdHHFzbs.r)({ uri: proxyUrl }, timeoutMs);
}
async function assertExplicitProxyAllowed(dispatcherPolicy, lookupFn, policy) {
  if (!dispatcherPolicy || dispatcherPolicy.mode !== "explicit-proxy") return;
  let parsedProxyUrl;
  try {
    parsedProxyUrl = new URL(dispatcherPolicy.proxyUrl);
  } catch {
    throw new Error("Invalid explicit proxy URL");
  }
  if (!["http:", "https:"].includes(parsedProxyUrl.protocol)) throw new Error("Explicit proxy URL must use http or https");
  const proxyPolicy = policy || dispatcherPolicy.allowPrivateProxy === true ? {
    ...policy,
    hostnameAllowlist: void 0,
    ...(dispatcherPolicy.allowPrivateProxy === true ? { allowPrivateNetwork: true } : {})
  } : void 0;
  await (0, _ssrfB5bGsnx.g)(parsedProxyUrl.hostname, {
    lookupFn,
    policy: proxyPolicy
  });
}
function isRedirectStatus(status) {
  return status === 301 || status === 302 || status === 303 || status === 307 || status === 308;
}
function isAmbientGlobalFetch(params) {
  return typeof params.fetchImpl === "function" && typeof params.globalFetch === "function" && params.fetchImpl === params.globalFetch;
}
function retainSafeHeadersForCrossOriginRedirectHeaders(headers) {
  return (0, _redirectHeadersCdvG9Jv.t)(headers);
}
function retainSafeHeadersForCrossOriginRedirect(init) {
  if (!init?.headers) return init;
  return {
    ...init,
    headers: (0, _redirectHeadersCdvG9Jv.t)(init.headers)
  };
}
function dropBodyHeaders(headers) {
  if (!headers) return headers;
  const nextHeaders = new Headers((0, _fetchHeadersDrgi2oEU.t)(headers));
  nextHeaders.delete("content-encoding");
  nextHeaders.delete("content-language");
  nextHeaders.delete("content-length");
  nextHeaders.delete("content-location");
  nextHeaders.delete("content-type");
  nextHeaders.delete("transfer-encoding");
  return nextHeaders;
}
function rewriteRedirectInitForMethod(params) {
  const { init, status } = params;
  if (!init) return init;
  const currentMethod = init.method?.toUpperCase() ?? "GET";
  if (!(status === 303 ? currentMethod !== "GET" && currentMethod !== "HEAD" : (status === 301 || status === 302) && currentMethod === "POST")) return init;
  return {
    ...init,
    method: "GET",
    body: void 0,
    headers: dropBodyHeaders(init.headers)
  };
}
function rewriteRedirectInitForCrossOrigin(params) {
  const { init, allowUnsafeReplay } = params;
  if (!init || allowUnsafeReplay) return init;
  const currentMethod = init.method?.toUpperCase() ?? "GET";
  if (currentMethod === "GET" || currentMethod === "HEAD") return init;
  return {
    ...init,
    body: void 0,
    headers: dropBodyHeaders(init.headers)
  };
}
async function fetchWithSsrFGuard(params) {
  const defaultFetch = params.fetchImpl ?? globalThis.fetch;
  if (!defaultFetch) throw new Error("fetch is not available");
  const maxRedirects = typeof params.maxRedirects === "number" && Number.isFinite(params.maxRedirects) ? Math.max(0, Math.floor(params.maxRedirects)) : DEFAULT_MAX_REDIRECTS;
  const mode = resolveGuardedFetchMode(params);
  const { signal, cleanup, refresh } = (0, _fetchTimeoutBJUkaK0F.n)({
    timeoutMs: params.timeoutMs,
    signal: params.signal,
    operation: "fetchWithSsrFGuard",
    url: params.url
  });
  let released = false;
  const release = async (dispatcher) => {
    if (released) return;
    released = true;
    cleanup();
    await (0, _ssrfB5bGsnx.i)(dispatcher ?? void 0);
  };
  const visited = new Set([params.url]);
  let currentUrl = params.url;
  let currentInit = (0, _fetchHeadersDrgi2oEU.n)(params.init ? { ...params.init } : void 0);
  let redirectCount = 0;
  while (true) {
    let parsedUrl;
    try {
      parsedUrl = new URL(currentUrl);
    } catch {
      await release();
      throw new Error("Invalid URL: must be http or https");
    }
    if (!["http:", "https:"].includes(parsedUrl.protocol)) {
      await release();
      throw new Error("Invalid URL: must be http or https");
    }
    if (params.requireHttps === true && parsedUrl.protocol !== "https:") {
      await release();
      throw new Error("URL must use https");
    }
    let dispatcher = null;
    try {
      const usesTrustedExplicitProxyMode = mode === GUARDED_FETCH_MODE.TRUSTED_EXPLICIT_PROXY && params.dispatcherPolicy?.mode === "explicit-proxy";
      assertExplicitProxySupportsPinnedDns(parsedUrl, params.dispatcherPolicy, usesTrustedExplicitProxyMode ? false : params.pinDns);
      await assertExplicitProxyAllowed(params.dispatcherPolicy, params.lookupFn, params.policy);
      const canUseTrustedEnvProxy = mode === GUARDED_FETCH_MODE.TRUSTED_ENV_PROXY && (0, _proxyEnvBaS80pvI.c)(parsedUrl.toString());
      const canUseManagedProxy = mode === GUARDED_FETCH_MODE.STRICT && isManagedProxyActive() && (0, _proxyEnvBaS80pvI.i)();
      const timeoutMs = resolveDispatcherTimeoutMs(params.timeoutMs);
      if (canUseTrustedEnvProxy || params.pinDns === false) (0, _ssrfB5bGsnx.n)(parsedUrl.hostname, params.policy);
      if (canUseTrustedEnvProxy) dispatcher = (0, _undiciRuntimeBdHHFzbs.n)(void 0, timeoutMs);else
      if (canUseManagedProxy) {
        await (0, _ssrfB5bGsnx.g)(parsedUrl.hostname, {
          lookupFn: params.lookupFn,
          policy: params.policy
        });
        dispatcher = (0, _undiciRuntimeBdHHFzbs.n)(void 0, timeoutMs);
      } else if (usesTrustedExplicitProxyMode) {
        (0, _ssrfB5bGsnx.n)(parsedUrl.hostname, params.policy);
        dispatcher = createPolicyDispatcherWithoutPinnedDns(params.dispatcherPolicy, timeoutMs);
      } else if (params.pinDns === false) {
        await (0, _ssrfB5bGsnx.g)(parsedUrl.hostname, {
          lookupFn: params.lookupFn,
          policy: params.policy
        });
        dispatcher = createPolicyDispatcherWithoutPinnedDns(params.dispatcherPolicy, timeoutMs);
      } else dispatcher = (0, _ssrfB5bGsnx.a)(await (0, _ssrfB5bGsnx.g)(parsedUrl.hostname, {
        lookupFn: params.lookupFn,
        policy: params.policy
      }), params.dispatcherPolicy, params.policy, timeoutMs);
      const init = {
        ...(currentInit ? { ...currentInit } : {}),
        redirect: "manual",
        ...(dispatcher ? { dispatcher } : {}),
        ...(signal ? { signal } : {})
      };
      const supportsDispatcherInit = params.fetchImpl !== void 0 && !isAmbientGlobalFetch({
        fetchImpl: params.fetchImpl,
        globalFetch: globalThis.fetch
      }) || (0, _runtimeFetchD8j2J4DT.r)(defaultFetch);
      const response = Boolean(dispatcher) && !supportsDispatcherInit ? await (0, _runtimeFetchD8j2J4DT.t)(parsedUrl.toString(), init) : await defaultFetch(parsedUrl.toString(), init);
      if (params.capture !== false) (0, _runtimeCHdWdufZ.t)({
        url: parsedUrl.toString(),
        method: currentInit?.method ?? "GET",
        requestHeaders: currentInit?.headers,
        requestBody: currentInit?.body ?? null,
        response,
        transport: "http",
        flowId: params.capture?.flowId,
        meta: {
          captureOrigin: "guarded-fetch",
          ...(params.auditContext ? { auditContext: params.auditContext } : {}),
          ...params.capture?.meta
        }
      });
      if (isRedirectStatus(response.status)) {
        const location = response.headers.get("location");
        if (!location) {
          await release(dispatcher);
          throw new Error(`Redirect missing location header (${response.status})`);
        }
        redirectCount += 1;
        if (redirectCount > maxRedirects) {
          await release(dispatcher);
          throw new Error(`Too many redirects (limit: ${maxRedirects})`);
        }
        const nextParsedUrl = new URL(location, parsedUrl);
        const nextUrl = nextParsedUrl.toString();
        if (visited.has(nextUrl)) {
          await release(dispatcher);
          throw new Error("Redirect loop detected");
        }
        currentInit = rewriteRedirectInitForMethod({
          init: currentInit,
          status: response.status
        });
        if (nextParsedUrl.origin !== parsedUrl.origin) {
          currentInit = rewriteRedirectInitForCrossOrigin({
            init: currentInit,
            allowUnsafeReplay: params.allowCrossOriginUnsafeRedirectReplay === true
          });
          currentInit = retainSafeHeadersForCrossOriginRedirect(currentInit);
        }
        visited.add(nextUrl);
        response.body?.cancel();
        await (0, _ssrfB5bGsnx.i)(dispatcher);
        currentUrl = nextUrl;
        continue;
      }
      return {
        response,
        finalUrl: currentUrl,
        release: async () => release(dispatcher),
        refreshTimeout: refresh
      };
    } catch (err) {
      if (err instanceof _ssrfB5bGsnx.t) (0, _loggerDksTYIAF.a)(`security: blocked URL fetch (${params.auditContext ?? "url-fetch"}) targetOrigin=${parsedUrl.origin} reason=${err.message}`);
      await release(dispatcher);
      throw err;
    }
  }
}
//#endregion /* v9-10a2021c7fdff745 */
