"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = replaceRuntimeAuthProfileStoreSnapshots;exports.c = resolveAuthStatePathForDisplay;exports.d = resolveLegacyAuthStorePath;exports.f = resolveOAuthRefreshLockPath;exports.i = hasRuntimeAuthProfileStoreSnapshot;exports.l = resolveAuthStorePath;exports.n = clearRuntimeAuthProfileStoreSnapshots;exports.o = setRuntimeAuthProfileStoreSnapshot;exports.p = cloneAuthProfileStore;exports.r = getRuntimeAuthProfileStoreSnapshot;exports.s = resolveAuthStatePath;exports.t = hasAnyAuthProfileStoreSource;exports.u = resolveAuthStorePathForDisplay;var _pathsC1_Y0cDn = require("./paths-C1_Y0cDn.js");
var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
var _agentPathsUmbOEWUL = require("./agent-paths-umbOEWUL.js");
var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));
var _nodeCrypto = require("node:crypto");function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/agents/auth-profiles/clone.ts
function cloneAuthProfileStore(store) {
  return JSON.parse(JSON.stringify(store, (_key, value) => {
    if (typeof value === "bigint" || typeof value === "function" || typeof value === "symbol") throw new TypeError(`AuthProfileStore contains non-JSON value: ${typeof value}`);
    return value;
  }));
}
//#endregion
//#region src/agents/auth-profiles/path-constants.ts
const AUTH_PROFILE_FILENAME = "auth-profiles.json";
const AUTH_STATE_FILENAME = "auth-state.json";
const LEGACY_AUTH_FILENAME = "auth.json";
//#endregion
//#region src/agents/auth-profiles/path-resolve.ts
function resolveAuthStorePath(agentDir) {
  const resolved = (0, _utilsD5swhEXt.p)(agentDir ?? (0, _agentPathsUmbOEWUL.t)());
  return _nodePath.default.join(resolved, AUTH_PROFILE_FILENAME);
}
function resolveLegacyAuthStorePath(agentDir) {
  const resolved = (0, _utilsD5swhEXt.p)(agentDir ?? (0, _agentPathsUmbOEWUL.t)());
  return _nodePath.default.join(resolved, LEGACY_AUTH_FILENAME);
}
function resolveAuthStatePath(agentDir) {
  const resolved = (0, _utilsD5swhEXt.p)(agentDir ?? (0, _agentPathsUmbOEWUL.t)());
  return _nodePath.default.join(resolved, AUTH_STATE_FILENAME);
}
function resolveAuthStorePathForDisplay(agentDir) {
  const pathname = resolveAuthStorePath(agentDir);
  return pathname.startsWith("~") ? pathname : (0, _utilsD5swhEXt.p)(pathname);
}
function resolveAuthStatePathForDisplay(agentDir) {
  const pathname = resolveAuthStatePath(agentDir);
  return pathname.startsWith("~") ? pathname : (0, _utilsD5swhEXt.p)(pathname);
}
/**
* Resolve the path of the cross-agent, per-profile OAuth refresh coordination
* lock. The filename hashes `provider\0profileId` so it is filesystem-safe
* for arbitrary unicode/control-character inputs and always bounded in
* length. The NUL separator makes it impossible to collide two distinct
* `(provider, profileId)` pairs by string concatenation.
*
* This lock is the serialization point that prevents the `refresh_token_reused`
* storm when N agents share one OAuth profile (see issue #26322): every agent
* that attempts a refresh acquires this same file lock, so only one HTTP
* refresh is in-flight at a time and peers can adopt the resulting fresh
* credentials instead of racing against a single-use refresh token.
*
* The key intentionally includes `provider` so that two profiles that
* happen to share a `profileId` across providers (operator-renamed profile,
* test fixture, etc.) do not needlessly serialize against each other.
*/
function resolveOAuthRefreshLockPath(provider, profileId) {
  const hash = (0, _nodeCrypto.createHash)("sha256");
  hash.update(provider, "utf8");
  hash.update("\0", "utf8");
  hash.update(profileId, "utf8");
  const safeId = `sha256-${hash.digest("hex")}`;
  return _nodePath.default.join((0, _pathsC1_Y0cDn.v)(), "locks", "oauth-refresh", safeId);
}
//#endregion
//#region src/agents/auth-profiles/runtime-snapshots.ts
const runtimeAuthStoreSnapshots = /* @__PURE__ */new Map();
function resolveRuntimeStoreKey(agentDir) {
  return resolveAuthStorePath(agentDir);
}
function getRuntimeAuthProfileStoreSnapshot(agentDir) {
  const store = runtimeAuthStoreSnapshots.get(resolveRuntimeStoreKey(agentDir));
  return store ? cloneAuthProfileStore(store) : void 0;
}
function hasRuntimeAuthProfileStoreSnapshot(agentDir) {
  return runtimeAuthStoreSnapshots.has(resolveRuntimeStoreKey(agentDir));
}
function hasAnyRuntimeAuthProfileStoreSource(agentDir) {
  const requestedStore = getRuntimeAuthProfileStoreSnapshot(agentDir);
  if (requestedStore && Object.keys(requestedStore.profiles).length > 0) return true;
  if (!agentDir) return false;
  const mainStore = getRuntimeAuthProfileStoreSnapshot();
  return Boolean(mainStore && Object.keys(mainStore.profiles).length > 0);
}
function replaceRuntimeAuthProfileStoreSnapshots(entries) {
  runtimeAuthStoreSnapshots.clear();
  for (const entry of entries) runtimeAuthStoreSnapshots.set(resolveRuntimeStoreKey(entry.agentDir), cloneAuthProfileStore(entry.store));
}
function clearRuntimeAuthProfileStoreSnapshots() {
  runtimeAuthStoreSnapshots.clear();
}
function setRuntimeAuthProfileStoreSnapshot(store, agentDir) {
  runtimeAuthStoreSnapshots.set(resolveRuntimeStoreKey(agentDir), cloneAuthProfileStore(store));
}
//#endregion
//#region src/agents/auth-profiles/source-check.ts
function hasStoredAuthProfileFiles(agentDir) {
  return _nodeFs.default.existsSync(resolveAuthStorePath(agentDir)) || _nodeFs.default.existsSync(resolveAuthStatePath(agentDir)) || _nodeFs.default.existsSync(resolveLegacyAuthStorePath(agentDir));
}
function hasAnyAuthProfileStoreSource(agentDir) {
  if (hasAnyRuntimeAuthProfileStoreSource(agentDir)) return true;
  if (hasStoredAuthProfileFiles(agentDir)) return true;
  const authPath = resolveAuthStorePath(agentDir);
  const mainAuthPath = resolveAuthStorePath();
  if (agentDir && authPath !== mainAuthPath && hasStoredAuthProfileFiles(void 0)) return true;
  return false;
}
//#endregion /* v9-38a0a9bc0b10a78f */
