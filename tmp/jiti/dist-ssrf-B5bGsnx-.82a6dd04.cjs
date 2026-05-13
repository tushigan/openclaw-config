"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports._ = ssrfPolicyFromHttpBaseUrlAllowedHostname;exports.a = createPinnedDispatcher;exports.c = isBlockedHostnameOrIp;exports.d = isPrivateNetworkAllowedByPolicy;exports.f = isSameSsrFPolicy;exports.g = resolvePinnedHostnameWithPolicy;exports.h = resolvePinnedHostname;exports.i = closeDispatcher;exports.l = isHostnameAllowedByPattern;exports.m = normalizeHostnameAllowlist;exports.n = assertHostnameAllowedWithPolicy;exports.o = createPinnedLookup;exports.p = matchesHostnameAllowlist;exports.r = assertPublicHostname;exports.s = isBlockedHostname;exports.t = void 0;exports.u = isPrivateIpAddress;exports.v = ssrfPolicyFromHttpBaseUrlFakeIpHostnameAllowlist;exports.y = void 0;var _chunkAJGZS = require("./chunk-A-jGZS85.js");
var _ip9c4ODEZi = require("./ip-9c4ODEZi.js");
var _undiciRuntimeBdHHFzbs = require("./undici-runtime-BdHHFzbs.js");
var _hostnameD7aD98O = require("./hostname-D7aD9-8O.js");
var _nodeDns = require("node:dns");
var _promises = require("node:dns/promises");
//#region src/infra/net/ssrf.ts
var ssrf_exports = exports.y = /* @__PURE__ */(0, _chunkAJGZS.r)({
  SsrFBlockedError: () => SsrFBlockedError,
  assertHostnameAllowedWithPolicy: () => assertHostnameAllowedWithPolicy,
  assertPublicHostname: () => assertPublicHostname,
  closeDispatcher: () => closeDispatcher,
  createPinnedDispatcher: () => createPinnedDispatcher,
  createPinnedLookup: () => createPinnedLookup,
  isBlockedHostname: () => isBlockedHostname,
  isBlockedHostnameOrIp: () => isBlockedHostnameOrIp,
  isHostnameAllowedByPattern: () => isHostnameAllowedByPattern,
  isPrivateIpAddress: () => isPrivateIpAddress,
  isPrivateNetworkAllowedByPolicy: () => isPrivateNetworkAllowedByPolicy,
  isSameSsrFPolicy: () => isSameSsrFPolicy,
  matchesHostnameAllowlist: () => matchesHostnameAllowlist,
  normalizeHostnameAllowlist: () => normalizeHostnameAllowlist,
  resolvePinnedHostname: () => resolvePinnedHostname,
  resolvePinnedHostnameWithPolicy: () => resolvePinnedHostnameWithPolicy,
  ssrfPolicyFromHttpBaseUrlAllowedHostname: () => ssrfPolicyFromHttpBaseUrlAllowedHostname,
  ssrfPolicyFromHttpBaseUrlFakeIpHostnameAllowlist: () => ssrfPolicyFromHttpBaseUrlFakeIpHostnameAllowlist
});
const DISPATCHER_CLOSE_TIMEOUT_MS = 100;
var SsrFBlockedError = class extends Error {
  constructor(message) {
    super(message);
    this.name = "SsrFBlockedError";
  }
};exports.t = SsrFBlockedError;
function normalizeSsrFPolicyHostnames(values) {
  if (!values || values.length === 0) return [];
  return Array.from(new Set(values.map((value) => (0, _hostnameD7aD98O.t)(value)).filter(Boolean))).toSorted();
}
function normalizeSsrFPolicyForComparison(policy) {
  if (!policy) return null;
  return {
    allowPrivateNetwork: policy.allowPrivateNetwork === true,
    dangerouslyAllowPrivateNetwork: policy.dangerouslyAllowPrivateNetwork === true,
    allowRfc2544BenchmarkRange: policy.allowRfc2544BenchmarkRange === true,
    allowIpv6UniqueLocalRange: policy.allowIpv6UniqueLocalRange === true,
    allowedHostnames: normalizeSsrFPolicyHostnames(policy.allowedHostnames),
    hostnameAllowlist: [...normalizeHostnameAllowlist(policy.hostnameAllowlist)].toSorted()
  };
}
function isSameSsrFPolicy(a, b) {
  return JSON.stringify(normalizeSsrFPolicyForComparison(a)) === JSON.stringify(normalizeSsrFPolicyForComparison(b));
}
function ssrfPolicyFromHttpBaseUrlAllowedHostname(baseUrl) {
  const trimmed = baseUrl.trim();
  if (!trimmed) return;
  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return;
    return { allowedHostnames: [parsed.hostname] };
  } catch {
    return;
  }
}
function ssrfPolicyFromHttpBaseUrlFakeIpHostnameAllowlist(baseUrl) {
  const trimmed = baseUrl.trim();
  if (!trimmed) return;
  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return;
    return {
      allowRfc2544BenchmarkRange: true,
      allowIpv6UniqueLocalRange: true,
      hostnameAllowlist: [parsed.hostname]
    };
  } catch {
    return;
  }
}
const BLOCKED_HOSTNAMES = new Set([
"localhost",
"localhost.localdomain",
"metadata.google.internal"]
);
function normalizeHostnameSet(values) {
  if (!values || values.length === 0) return /* @__PURE__ */new Set();
  return new Set(values.map((value) => (0, _hostnameD7aD98O.t)(value)).filter(Boolean));
}
function normalizeHostnameAllowlist(values) {
  if (!values || values.length === 0) return [];
  return Array.from(new Set(values.map((value) => (0, _hostnameD7aD98O.t)(value)).filter((value) => value !== "*" && value !== "*." && value.length > 0)));
}
function isPrivateNetworkAllowedByPolicy(policy) {
  return policy?.dangerouslyAllowPrivateNetwork === true || policy?.allowPrivateNetwork === true;
}
function shouldSkipPrivateNetworkChecks(hostname, policy) {
  return isPrivateNetworkAllowedByPolicy(policy) || normalizeHostnameSet(policy?.allowedHostnames).has(hostname);
}
function resolveIpv4SpecialUseBlockOptions(policy) {
  return { allowRfc2544BenchmarkRange: policy?.allowRfc2544BenchmarkRange === true };
}
function resolveIpv6SpecialUseBlockOptions(policy) {
  return { allowUniqueLocalRange: policy?.allowIpv6UniqueLocalRange === true };
}
function isHostnameAllowedByPattern(hostname, pattern) {
  if (pattern.startsWith("*.")) {
    const suffix = pattern.slice(2);
    if (!suffix || hostname === suffix) return false;
    return hostname.endsWith(`.${suffix}`);
  }
  return hostname === pattern;
}
function matchesHostnameAllowlist(hostname, allowlist) {
  if (allowlist.length === 0) return true;
  return allowlist.some((pattern) => isHostnameAllowedByPattern(hostname, pattern));
}
function looksLikeUnsupportedIpv4Literal(address) {
  const parts = address.split(".");
  if (parts.length === 0 || parts.length > 4) return false;
  if (parts.some((part) => part.length === 0)) return true;
  return parts.every((part) => /^[0-9]+$/.test(part) || /^0x/i.test(part));
}
function isPrivateIpAddress(address, policy) {
  const normalized = (0, _hostnameD7aD98O.t)(address);
  if (!normalized) return false;
  const blockOptions = resolveIpv4SpecialUseBlockOptions(policy);
  const ipv6BlockOptions = resolveIpv6SpecialUseBlockOptions(policy);
  const strictIp = (0, _ip9c4ODEZi.m)(normalized);
  if (strictIp) {
    if ((0, _ip9c4ODEZi.s)(strictIp)) return (0, _ip9c4ODEZi.n)(strictIp, blockOptions);
    if ((0, _ip9c4ODEZi.r)(strictIp, ipv6BlockOptions)) return true;
    const embeddedIpv4 = (0, _ip9c4ODEZi.t)(strictIp);
    if (embeddedIpv4) return (0, _ip9c4ODEZi.n)(embeddedIpv4, blockOptions);
    return false;
  }
  if (normalized.includes(":") && !(0, _ip9c4ODEZi.h)(normalized)) return true;
  if (!(0, _ip9c4ODEZi.i)(normalized) && (0, _ip9c4ODEZi.l)(normalized)) return true;
  if (looksLikeUnsupportedIpv4Literal(normalized)) return true;
  return false;
}
function isBlockedHostname(hostname) {
  const normalized = (0, _hostnameD7aD98O.t)(hostname);
  if (!normalized) return false;
  return isBlockedHostnameNormalized(normalized);
}
function isBlockedHostnameNormalized(normalized) {
  if (BLOCKED_HOSTNAMES.has(normalized)) return true;
  return normalized.endsWith(".localhost") || normalized.endsWith(".local") || normalized.endsWith(".internal");
}
function isBlockedHostnameOrIp(hostname, policy) {
  const normalized = (0, _hostnameD7aD98O.t)(hostname);
  if (!normalized) return false;
  return isBlockedHostnameNormalized(normalized) || isPrivateIpAddress(normalized, policy);
}
const BLOCKED_HOST_OR_IP_MESSAGE = "Blocked hostname or private/internal/special-use IP address";
const BLOCKED_RESOLVED_IP_MESSAGE = "Blocked: resolves to private/internal/special-use IP address";
function assertAllowedHostOrIpOrThrow(hostnameOrIp, policy) {
  if (isBlockedHostnameOrIp(hostnameOrIp, policy)) throw new SsrFBlockedError(BLOCKED_HOST_OR_IP_MESSAGE);
}
function resolveHostnamePolicyChecks(hostname, policy) {
  const normalized = (0, _hostnameD7aD98O.t)(hostname);
  if (!normalized) throw new Error("Invalid hostname");
  const hostnameAllowlist = normalizeHostnameAllowlist(policy?.hostnameAllowlist);
  const skipPrivateNetworkChecks = shouldSkipPrivateNetworkChecks(normalized, policy);
  if (!matchesHostnameAllowlist(normalized, hostnameAllowlist)) throw new SsrFBlockedError(`Blocked hostname (not in allowlist): ${hostname}`);
  if (!skipPrivateNetworkChecks) assertAllowedHostOrIpOrThrow(normalized, policy);
  return {
    normalized,
    skipPrivateNetworkChecks
  };
}
function assertAllowedResolvedAddressesOrThrow(results, policy) {
  for (const entry of results) if (isBlockedHostnameOrIp(entry.address, policy)) throw new SsrFBlockedError(BLOCKED_RESOLVED_IP_MESSAGE);
}
function normalizeLookupResults(results) {
  if (Array.isArray(results)) return results;
  return [results];
}
function createPinnedLookup(params) {
  const normalizedHost = (0, _hostnameD7aD98O.t)(params.hostname);
  if (params.addresses.length === 0) throw new Error(`Pinned lookup requires at least one address for ${params.hostname}`);
  const fallback = params.fallback ?? _nodeDns.lookup;
  const fallbackLookup = fallback;
  const fallbackWithOptions = fallback;
  const records = params.addresses.map((address) => ({
    address,
    family: address.includes(":") ? 6 : 4
  }));
  let index = 0;
  return (host, options, callback) => {
    const cb = typeof options === "function" ? options : callback;
    if (!cb) return;
    const normalized = (0, _hostnameD7aD98O.t)(host);
    if (!normalized || normalized !== normalizedHost) {
      if (typeof options === "function" || options === void 0) return fallbackLookup(host, cb);
      return fallbackWithOptions(host, options, cb);
    }
    const opts = typeof options === "object" && options !== null ? options : {};
    const requestedFamily = typeof options === "number" ? options : typeof opts.family === "number" ? opts.family : 0;
    const candidates = requestedFamily === 4 || requestedFamily === 6 ? records.filter((entry) => entry.family === requestedFamily) : records;
    const usable = candidates.length > 0 ? candidates : records;
    if (opts.all) {
      cb(null, usable);
      return;
    }
    const chosen = usable[index % usable.length];
    index += 1;
    cb(null, chosen.address, chosen.family);
  };
}
function dedupeAndPreferIpv4(results) {
  const seen = /* @__PURE__ */new Set();
  const ipv4 = [];
  const otherFamilies = [];
  for (const entry of results) {
    if (seen.has(entry.address)) continue;
    seen.add(entry.address);
    if (entry.family === 4) {
      ipv4.push(entry.address);
      continue;
    }
    otherFamilies.push(entry.address);
  }
  return [...ipv4, ...otherFamilies];
}
async function resolvePinnedHostnameWithPolicy(hostname, params = {}) {
  const { normalized, skipPrivateNetworkChecks } = resolveHostnamePolicyChecks(hostname, params.policy);
  const results = normalizeLookupResults(await (params.lookupFn ?? _promises.lookup)(normalized, { all: true }));
  if (results.length === 0) throw new Error(`Unable to resolve hostname: ${hostname}`);
  if (!skipPrivateNetworkChecks) assertAllowedResolvedAddressesOrThrow(results, params.policy);
  const addresses = dedupeAndPreferIpv4(results);
  if (addresses.length === 0) throw new Error(`Unable to resolve hostname: ${hostname}`);
  return {
    hostname: normalized,
    addresses,
    lookup: createPinnedLookup({
      hostname: normalized,
      addresses
    })
  };
}
function assertHostnameAllowedWithPolicy(hostname, policy) {
  return resolveHostnamePolicyChecks(hostname, policy).normalized;
}
async function resolvePinnedHostname(hostname, lookupFn = _promises.lookup) {
  return await resolvePinnedHostnameWithPolicy(hostname, { lookupFn });
}
function withPinnedLookup(lookup, connect) {
  return connect ? {
    ...connect,
    lookup
  } : { lookup };
}
function resolvePinnedDispatcherLookup(pinned, override, policy) {
  if (!override) return pinned.lookup;
  const normalizedOverrideHost = (0, _hostnameD7aD98O.t)(override.hostname);
  if (!normalizedOverrideHost || normalizedOverrideHost !== pinned.hostname) throw new Error(`Pinned dispatcher override hostname mismatch: expected ${pinned.hostname}, got ${override.hostname}`);
  const records = override.addresses.map((address) => ({
    address,
    family: address.includes(":") ? 6 : 4
  }));
  if (!shouldSkipPrivateNetworkChecks(pinned.hostname, policy)) assertAllowedResolvedAddressesOrThrow(records, policy);
  return createPinnedLookup({
    hostname: pinned.hostname,
    addresses: [...override.addresses],
    fallback: pinned.lookup
  });
}
function createPinnedDispatcher(pinned, policy, ssrfPolicy, timeoutMs) {
  const lookup = resolvePinnedDispatcherLookup(pinned, policy?.pinnedHostname, ssrfPolicy);
  if (!policy || policy.mode === "direct") return (0, _undiciRuntimeBdHHFzbs.t)({ connect: withPinnedLookup(lookup, policy?.connect) }, timeoutMs);
  if (policy.mode === "env-proxy") return (0, _undiciRuntimeBdHHFzbs.n)({
    connect: withPinnedLookup(lookup, policy.connect),
    ...(policy.proxyTls ? { proxyTls: { ...policy.proxyTls } } : {})
  }, timeoutMs);
  const proxyUrl = policy.proxyUrl.trim();
  const requestTls = withPinnedLookup(lookup, policy.proxyTls);
  if (!requestTls) return (0, _undiciRuntimeBdHHFzbs.r)({ uri: proxyUrl }, timeoutMs);
  return (0, _undiciRuntimeBdHHFzbs.r)({
    uri: proxyUrl,
    requestTls
  }, timeoutMs);
}
function destroyDispatcher(candidate) {
  try {
    candidate.destroy?.();
  } catch {}
}
async function waitForDispatcherClose(candidate) {
  const close = candidate.close;
  if (typeof close !== "function") {
    destroyDispatcher(candidate);
    return;
  }
  let timeout;
  try {
    await Promise.race([Promise.resolve(close.call(candidate)), new Promise((resolve) => {
      timeout = setTimeout(() => {
        timeout = void 0;
        destroyDispatcher(candidate);
        resolve();
      }, DISPATCHER_CLOSE_TIMEOUT_MS);
      timeout.unref?.();
    })]);
  } catch (err) {
    destroyDispatcher(candidate);
    throw err;
  } finally {
    if (timeout) clearTimeout(timeout);
  }
}
async function closeDispatcher(dispatcher) {
  if (!dispatcher) return;
  const candidate = dispatcher;
  try {
    await waitForDispatcherClose(candidate);
  } catch {}
}
async function assertPublicHostname(hostname, lookupFn = _promises.lookup) {
  await resolvePinnedHostname(hostname, lookupFn);
}
//#endregion /* v9-3502b24ac41d06ec */
