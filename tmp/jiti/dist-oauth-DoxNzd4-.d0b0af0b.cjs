"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveEffectiveOAuthCredential;exports.r = formatAuthDoctorHint;exports.t = resolveApiKeyForProfile;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _errorsQN8rySzW = require("./errors-QN8rySzW.js");
var _typesSecretsCL51SR4g = require("./types.secrets-CL51SR4g.js");
var _providerIdDIRgKpoh = require("./provider-id-DIRgKpoh.js");
var _resolveCqhiFUTe = require("./resolve-CqhiFUTe.js");
var _ioE69J4lLI = require("./io-E69J4lLI.js");
require("./config-Dq84uU6c.js");
var _fileLockCqxhL0b = require("./file-lock-CqxhL0b-.js");
require("./file-lock-C8-Vkrrw.js");
var _sourceCheckBp0rrZbJ = require("./source-check-Bp0rrZbJ.js");
var _storeCSOk8Bno = require("./store-CSOk8Bno.js");
var _providerRuntimeRuntime = require("./provider-runtime.runtime.js");
var _chutesOauthDaeyYKYr = require("./chutes-oauth-DaeyYKYr.js");
var _policyDJ7xi3jO = require("./policy-DJ7xi3jO.js");
var _repairBvCst = require("./repair-BvCst034.js");
var _oauth = require("@mariozechner/pi-ai/oauth");
//#region src/agents/auth-profiles/doctor.ts
/**
* Migration hints for deprecated/removed OAuth providers.
* Users with stale credentials should be guided to migrate.
*/
const DEPRECATED_PROVIDER_MIGRATION_HINTS = { "qwen-portal": "Qwen OAuth via portal.qwen.ai has been deprecated. Please migrate to Qwen Cloud Coding Plan. Run: openclaw onboard --auth-choice qwen-api-key (or qwen-api-key-cn for the China endpoint). Legacy modelstudio auth-choice ids still work." };
async function formatAuthDoctorHint(params) {
  const normalizedProvider = (0, _providerIdDIRgKpoh.r)(params.provider);
  const migrationHint = DEPRECATED_PROVIDER_MIGRATION_HINTS[normalizedProvider];
  if (migrationHint) return migrationHint;
  const pluginHint = await (0, _providerRuntimeRuntime.n)({
    provider: normalizedProvider,
    context: {
      config: params.cfg,
      store: params.store,
      provider: normalizedProvider,
      profileId: params.profileId
    }
  });
  if (typeof pluginHint === "string" && pluginHint.trim()) return pluginHint;
  return "";
}
//#endregion
//#region src/agents/auth-profiles/oauth-identity.ts
function normalizeAuthIdentityToken(value) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : void 0;
}
function normalizeAuthEmailToken(value) {
  return normalizeAuthIdentityToken(value)?.toLowerCase();
}
/**
* One-sided copy gate for both directions:
* - mirror: sub-agent refresh -> main-agent store
* - adopt: main-agent store -> sub-agent store
*/
function isSafeToCopyOAuthIdentity(existing, incoming) {
  const aAcct = normalizeAuthIdentityToken(existing.accountId);
  const bAcct = normalizeAuthIdentityToken(incoming.accountId);
  const aEmail = normalizeAuthEmailToken(existing.email);
  const bEmail = normalizeAuthEmailToken(incoming.email);
  if (aAcct !== void 0 && bAcct !== void 0) return aAcct === bAcct;
  if (aEmail !== void 0 && bEmail !== void 0) return aEmail === bEmail;
  if (aAcct !== void 0 || aEmail !== void 0) return false;
  return true;
}
function shouldMirrorRefreshedOAuthCredential(params) {
  const { existing, refreshed } = params;
  if (!existing) return {
    shouldMirror: true,
    reason: "no-existing-credential"
  };
  if (existing.type !== "oauth") return {
    shouldMirror: false,
    reason: "non-oauth-existing-credential"
  };
  if (existing.provider !== refreshed.provider) return {
    shouldMirror: false,
    reason: "provider-mismatch"
  };
  if (!isSafeToCopyOAuthIdentity(existing, refreshed)) return {
    shouldMirror: false,
    reason: "identity-mismatch-or-regression"
  };
  if (Number.isFinite(existing.expires) && Number.isFinite(refreshed.expires) && existing.expires >= refreshed.expires) return {
    shouldMirror: false,
    reason: "incoming-not-fresher"
  };
  return {
    shouldMirror: true,
    reason: "incoming-fresher"
  };
}
//#endregion
//#region src/agents/auth-profiles/oauth-refresh-lock-errors.ts
function isGlobalRefreshLockTimeoutError(error, lockPath) {
  const candidate = typeof error === "object" && error !== null ? error : void 0;
  return candidate?.code === "file_lock_timeout" && candidate.lockPath === `${lockPath}.lock`;
}
function buildRefreshContentionError(params) {
  return Object.assign(new Error(`OAuth refresh failed (refresh_contention): another process is already refreshing ${params.provider} for ${params.profileId}. Please wait for the in-flight refresh to finish and retry.`, { cause: params.cause }), {
    code: "refresh_contention",
    cause: params.cause
  });
}
//#endregion
//#region src/agents/auth-profiles/oauth-manager.ts
var OAuthManagerRefreshError = class extends Error {
  #refreshedStore;
  #credential;
  constructor(params) {
    const structuredCause = typeof params.cause === "object" && params.cause !== null ? params.cause : void 0;
    const delegatedCause = structuredCause?.code === "refresh_contention" && structuredCause.cause ? structuredCause.cause : params.cause;
    super(`OAuth token refresh failed for ${params.credential.provider}: ${(0, _errorsQN8rySzW.i)(params.cause)}`, { cause: delegatedCause });
    this.name = "OAuthManagerRefreshError";
    this.#credential = params.credential;
    this.profileId = params.profileId;
    this.provider = params.credential.provider;
    this.#refreshedStore = params.refreshedStore;
    if (structuredCause) {
      this.code = typeof structuredCause.code === "string" ? structuredCause.code : void 0;
      if (typeof structuredCause.lockPath === "string") this.lockPath = structuredCause.lockPath;else
      if (typeof structuredCause.cause === "object" && structuredCause.cause !== null && "lockPath" in structuredCause.cause && typeof structuredCause.cause.lockPath === "string") this.lockPath = structuredCause.cause.lockPath;
    }
  }
  getRefreshedStore() {
    return this.#refreshedStore;
  }
  getCredential() {
    return this.#credential;
  }
  toJSON() {
    return {
      name: this.name,
      message: this.message,
      profileId: this.profileId,
      provider: this.provider
    };
  }
};
function hasOAuthCredentialChanged(previous, current) {
  return previous.access !== current.access || previous.refresh !== current.refresh || previous.expires !== current.expires;
}
async function loadFreshStoredOAuthCredential(params) {
  const reloaded = (0, _storeCSOk8Bno.l)(params.agentDir).profiles[params.profileId];
  if (reloaded?.type !== "oauth" || reloaded.provider !== params.provider || !(0, _storeCSOk8Bno.y)(reloaded)) return null;
  if (params.requireChange && params.previous && !hasOAuthCredentialChanged(params.previous, reloaded)) return null;
  return reloaded;
}
function resolveEffectiveOAuthCredential(params) {
  const imported = params.readBootstrapCredential({
    profileId: params.profileId,
    credential: params.credential
  });
  if (!imported) return params.credential;
  if ((0, _storeCSOk8Bno.y)(params.credential)) {
    _storeCSOk8Bno.I.debug("resolved oauth credential from canonical local store", {
      profileId: params.profileId,
      provider: params.credential.provider,
      localExpires: params.credential.expires,
      externalExpires: imported.expires
    });
    return params.credential;
  }
  if (!(0, _storeCSOk8Bno.b)(params.credential, imported)) {
    _storeCSOk8Bno.I.warn("refused external oauth bootstrap credential: identity mismatch or missing binding", {
      profileId: params.profileId,
      provider: params.credential.provider
    });
    return params.credential;
  }
  if ((0, _storeCSOk8Bno.S)({
    existing: params.credential,
    imported
  })) {
    _storeCSOk8Bno.I.debug("resolved oauth credential from external cli bootstrap", {
      profileId: params.profileId,
      provider: imported.provider,
      localExpires: params.credential.expires,
      externalExpires: imported.expires
    });
    return imported;
  }
  return params.credential;
}
function createOAuthManager(adapter) {
  function adoptNewerMainOAuthCredential(params) {
    if (!params.agentDir) return null;
    try {
      const mainCred = (0, _storeCSOk8Bno.i)(void 0, { allowKeychainPrompt: false }).profiles[params.profileId];
      if (mainCred?.type === "oauth" && mainCred.provider === params.credential.provider && (0, _storeCSOk8Bno.y)(mainCred) && Number.isFinite(mainCred.expires) && (!Number.isFinite(params.credential.expires) || mainCred.expires > params.credential.expires) && (0, _storeCSOk8Bno.x)(params.credential, mainCred)) {
        params.store.profiles[params.profileId] = { ...mainCred };
        _storeCSOk8Bno.I.info("adopted newer OAuth credentials from main agent", {
          profileId: params.profileId,
          agentDir: params.agentDir,
          expires: new Date(mainCred.expires).toISOString()
        });
        return mainCred;
      }
    } catch (err) {
      _storeCSOk8Bno.I.debug("adoptNewerMainOAuthCredential failed", {
        profileId: params.profileId,
        error: (0, _errorsQN8rySzW.i)(err)
      });
    }
    return null;
  }
  const refreshQueues = /* @__PURE__ */new Map();
  function refreshQueueKey(provider, profileId) {
    return `${provider}\u0000${profileId}`;
  }
  async function withRefreshCallTimeout(label, timeoutMs, fn) {
    let timeoutHandle;
    try {
      return await new Promise((resolve, reject) => {
        timeoutHandle = setTimeout(() => {
          reject(/* @__PURE__ */new Error(`OAuth refresh call "${label}" exceeded hard timeout (${timeoutMs}ms)`));
        }, timeoutMs);
        fn().then(resolve, reject);
      });
    } finally {
      if (timeoutHandle) clearTimeout(timeoutHandle);
    }
  }
  async function mirrorRefreshedCredentialIntoMainStore(params) {
    try {
      (0, _storeCSOk8Bno.g)((0, _sourceCheckBp0rrZbJ.l)(void 0));
      await (0, _storeCSOk8Bno.p)({
        agentDir: void 0,
        updater: (store) => {
          const existing = store.profiles[params.profileId];
          const decision = shouldMirrorRefreshedOAuthCredential({
            existing,
            refreshed: params.refreshed
          });
          if (!decision.shouldMirror) {
            if (decision.reason === "identity-mismatch-or-regression") _storeCSOk8Bno.I.warn("refused to mirror OAuth credential: identity mismatch or regression", { profileId: params.profileId });
            return false;
          }
          store.profiles[params.profileId] = { ...params.refreshed };
          _storeCSOk8Bno.I.debug("mirrored refreshed OAuth credential to main agent store", {
            profileId: params.profileId,
            expires: Number.isFinite(params.refreshed.expires) ? new Date(params.refreshed.expires).toISOString() : void 0
          });
          return true;
        }
      });
    } catch (err) {
      _storeCSOk8Bno.I.debug("mirrorRefreshedCredentialIntoMainStore failed", {
        profileId: params.profileId,
        error: (0, _errorsQN8rySzW.i)(err)
      });
    }
  }
  async function doRefreshOAuthTokenWithLock(params) {
    const ownerAgentDir = (0, _storeCSOk8Bno.d)(params);
    const authPath = (0, _sourceCheckBp0rrZbJ.l)(ownerAgentDir);
    (0, _storeCSOk8Bno.g)(authPath);
    const globalRefreshLockPath = (0, _sourceCheckBp0rrZbJ.f)(params.provider, params.profileId);
    try {
      return await (0, _fileLockCqxhL0b.a)(globalRefreshLockPath, _storeCSOk8Bno.F, async () => (0, _fileLockCqxhL0b.a)(authPath, _storeCSOk8Bno.j, async () => {
        const store = (0, _storeCSOk8Bno.l)(ownerAgentDir);
        const cred = store.profiles[params.profileId];
        if (!cred || cred.type !== "oauth") return null;
        let credentialToRefresh = cred;
        if ((0, _storeCSOk8Bno.y)(cred)) return {
          apiKey: await adapter.buildApiKey(cred.provider, cred, {
            cfg: params.cfg,
            agentDir: params.agentDir
          }),
          credential: cred
        };
        if (params.agentDir) try {
          const mainCred = (0, _storeCSOk8Bno.l)(void 0).profiles[params.profileId];
          if (mainCred?.type === "oauth" && mainCred.provider === cred.provider && (0, _storeCSOk8Bno.y)(mainCred) && (0, _storeCSOk8Bno.x)(cred, mainCred)) {
            store.profiles[params.profileId] = { ...mainCred };
            _storeCSOk8Bno.I.info("adopted fresh OAuth credential from main store (under refresh lock)", {
              profileId: params.profileId,
              agentDir: params.agentDir,
              expires: new Date(mainCred.expires).toISOString()
            });
            return {
              apiKey: await adapter.buildApiKey(mainCred.provider, mainCred, {
                cfg: params.cfg,
                agentDir: params.agentDir
              }),
              credential: mainCred
            };
          } else if (mainCred?.type === "oauth" && mainCred.provider === cred.provider && (0, _storeCSOk8Bno.y)(mainCred) && !(0, _storeCSOk8Bno.x)(cred, mainCred)) _storeCSOk8Bno.I.warn("refused to adopt fresh main-store OAuth credential: identity mismatch", {
            profileId: params.profileId,
            agentDir: params.agentDir
          });
        } catch (err) {
          _storeCSOk8Bno.I.debug("inside-lock main-store adoption failed; proceeding to refresh", {
            profileId: params.profileId,
            error: (0, _errorsQN8rySzW.i)(err)
          });
        }
        const externallyManaged = adapter.readBootstrapCredential({
          profileId: params.profileId,
          credential: cred
        });
        if (externallyManaged) if (externallyManaged.provider !== cred.provider) _storeCSOk8Bno.I.warn("refused external oauth bootstrap credential: provider mismatch", {
          profileId: params.profileId,
          provider: cred.provider
        });else
        if (!(0, _storeCSOk8Bno.b)(cred, externallyManaged)) _storeCSOk8Bno.I.warn("refused external oauth bootstrap credential: identity mismatch or missing binding", {
          profileId: params.profileId,
          provider: cred.provider
        });else
        {
          if ((0, _storeCSOk8Bno.C)(cred, externallyManaged) && !(0, _storeCSOk8Bno.v)(cred, externallyManaged)) {
            store.profiles[params.profileId] = { ...externallyManaged };
            (0, _storeCSOk8Bno.f)(store, ownerAgentDir);
          }
          credentialToRefresh = externallyManaged;
          if ((0, _storeCSOk8Bno.y)(externallyManaged)) return {
            apiKey: await adapter.buildApiKey(externallyManaged.provider, externallyManaged, {
              cfg: params.cfg,
              agentDir: params.agentDir
            }),
            credential: externallyManaged
          };
        }
        const refreshedCredentials = await withRefreshCallTimeout(`refreshOAuthCredential(${cred.provider})`, _storeCSOk8Bno.P, async () => {
          const refreshed = await adapter.refreshCredential(credentialToRefresh);
          return refreshed ? {
            ...credentialToRefresh,
            ...refreshed,
            type: "oauth"
          } : null;
        });
        if (!refreshedCredentials) return null;
        store.profiles[params.profileId] = refreshedCredentials;
        (0, _storeCSOk8Bno.f)(store, ownerAgentDir);
        if (ownerAgentDir) {
          if ((0, _sourceCheckBp0rrZbJ.l)(void 0) !== authPath) await mirrorRefreshedCredentialIntoMainStore({
            profileId: params.profileId,
            refreshed: refreshedCredentials
          });
        }
        return {
          apiKey: await adapter.buildApiKey(cred.provider, refreshedCredentials, {
            cfg: params.cfg,
            agentDir: params.agentDir
          }),
          credential: refreshedCredentials
        };
      }));
    } catch (error) {
      if (isGlobalRefreshLockTimeoutError(error, globalRefreshLockPath)) throw buildRefreshContentionError({
        provider: params.provider,
        profileId: params.profileId,
        cause: error
      });
      throw error;
    }
  }
  async function refreshOAuthTokenWithLock(params) {
    const key = refreshQueueKey(params.provider, params.profileId);
    const prev = refreshQueues.get(key) ?? Promise.resolve();
    let release;
    const gate = new Promise((resolve) => {
      release = resolve;
    });
    refreshQueues.set(key, gate);
    try {
      await prev;
      return await doRefreshOAuthTokenWithLock(params);
    } finally {
      release();
      if (refreshQueues.get(key) === gate) refreshQueues.delete(key);
    }
  }
  async function resolveOAuthAccess(params) {
    const adoptedCredential = adoptNewerMainOAuthCredential({
      store: params.store,
      profileId: params.profileId,
      agentDir: params.agentDir,
      credential: params.credential
    }) ?? params.credential;
    const effectiveCredential = resolveEffectiveOAuthCredential({
      profileId: params.profileId,
      credential: adoptedCredential,
      readBootstrapCredential: adapter.readBootstrapCredential
    });
    if ((0, _storeCSOk8Bno.y)(effectiveCredential)) return {
      apiKey: await adapter.buildApiKey(effectiveCredential.provider, effectiveCredential, {
        cfg: params.cfg,
        agentDir: params.agentDir
      }),
      credential: effectiveCredential
    };
    try {
      return await refreshOAuthTokenWithLock({
        profileId: params.profileId,
        provider: params.credential.provider,
        agentDir: params.agentDir,
        cfg: params.cfg
      });
    } catch (error) {
      const refreshedStore = (0, _storeCSOk8Bno.l)(params.agentDir);
      const refreshed = refreshedStore.profiles[params.profileId];
      if (refreshed?.type === "oauth" && (0, _storeCSOk8Bno.y)(refreshed)) return {
        apiKey: await adapter.buildApiKey(refreshed.provider, refreshed, {
          cfg: params.cfg,
          agentDir: params.agentDir
        }),
        credential: refreshed
      };
      if (adapter.isRefreshTokenReusedError(error) && refreshed?.type === "oauth" && refreshed.provider === params.credential.provider && hasOAuthCredentialChanged(params.credential, refreshed)) {
        const recovered = await loadFreshStoredOAuthCredential({
          profileId: params.profileId,
          agentDir: params.agentDir,
          provider: params.credential.provider,
          previous: params.credential,
          requireChange: true
        });
        if (recovered) return {
          apiKey: await adapter.buildApiKey(recovered.provider, recovered, {
            cfg: params.cfg,
            agentDir: params.agentDir
          }),
          credential: recovered
        };
        try {
          const retried = await refreshOAuthTokenWithLock({
            profileId: params.profileId,
            provider: params.credential.provider,
            agentDir: params.agentDir,
            cfg: params.cfg
          });
          if (retried) return retried;
        } catch {}
      }
      if (params.agentDir) try {
        const mainCred = (0, _storeCSOk8Bno.i)(void 0, { allowKeychainPrompt: false }).profiles[params.profileId];
        if (mainCred?.type === "oauth" && mainCred.provider === params.credential.provider && (0, _storeCSOk8Bno.y)(mainCred) && (0, _storeCSOk8Bno.x)(params.credential, mainCred)) {
          refreshedStore.profiles[params.profileId] = { ...mainCred };
          _storeCSOk8Bno.I.info("inherited fresh OAuth credentials from main agent", {
            profileId: params.profileId,
            agentDir: params.agentDir,
            expires: new Date(mainCred.expires).toISOString()
          });
          return {
            apiKey: await adapter.buildApiKey(mainCred.provider, mainCred, {
              cfg: params.cfg,
              agentDir: params.agentDir
            }),
            credential: mainCred
          };
        }
      } catch {}
      throw new OAuthManagerRefreshError({
        credential: params.credential,
        profileId: params.profileId,
        refreshedStore,
        cause: error
      });
    }
  }
  function resetRefreshQueuesForTest() {
    refreshQueues.clear();
  }
  return {
    resolveOAuthAccess,
    resetRefreshQueuesForTest
  };
}
//#endregion
//#region src/agents/auth-profiles/oauth.ts
function listOAuthProviderIds() {
  if (typeof _oauth.getOAuthProviders !== "function") return [];
  const providers = (0, _oauth.getOAuthProviders)();
  if (!Array.isArray(providers)) return [];
  return providers.map((provider) => provider && typeof provider === "object" && "id" in provider && typeof provider.id === "string" ? provider.id : void 0).filter((providerId) => typeof providerId === "string");
}
const OAUTH_PROVIDER_IDS = new Set(listOAuthProviderIds());
const isOAuthProvider = (provider) => OAUTH_PROVIDER_IDS.has(provider);
const resolveOAuthProvider = (provider) => isOAuthProvider(provider) ? provider : null;
/** Bearer-token auth modes that are interchangeable (oauth tokens and raw tokens). */
const BEARER_AUTH_MODES = new Set(["oauth", "token"]);
const isCompatibleModeType = (mode, type) => {
  if (!mode || !type) return false;
  if (mode === type) return true;
  return BEARER_AUTH_MODES.has(mode) && BEARER_AUTH_MODES.has(type);
};
function isProfileConfigCompatible(params) {
  const profileConfig = params.cfg?.auth?.profiles?.[params.profileId];
  if (profileConfig && profileConfig.provider !== params.provider) return false;
  if (profileConfig && !isCompatibleModeType(profileConfig.mode, params.mode)) return false;
  return true;
}
async function buildOAuthApiKey(provider, credentials, context) {
  const formatted = await (0, _providerRuntimeRuntime.i)({
    provider,
    config: context.cfg,
    context: credentials
  });
  return typeof formatted === "string" && formatted.length > 0 ? formatted : credentials.access;
}
function buildApiKeyProfileResult(params) {
  return {
    apiKey: params.apiKey,
    provider: params.provider,
    email: params.email
  };
}
function extractErrorMessage(error) {
  return (0, _errorsQN8rySzW.i)(error);
}
function isRefreshTokenReusedError(error) {
  const message = (0, _stringCoerceBje8XVt.a)(extractErrorMessage(error));
  return message.includes("refresh_token_reused") || message.includes("refresh token has already been used") || message.includes("already been used to generate a new access token");
}
async function refreshOAuthCredential(credential) {
  const pluginRefreshed = await (0, _providerRuntimeRuntime.o)({
    provider: credential.provider,
    context: credential
  });
  if (pluginRefreshed) return pluginRefreshed;
  if (credential.provider === "chutes") return await (0, _chutesOauthDaeyYKYr.a)({ credential });
  const oauthProvider = resolveOAuthProvider(credential.provider);
  if (!oauthProvider || typeof _oauth.getOAuthApiKey !== "function") return null;
  return (await (0, _oauth.getOAuthApiKey)(oauthProvider, { [credential.provider]: credential }))?.newCredentials ?? null;
}
const oauthManager = createOAuthManager({
  buildApiKey: buildOAuthApiKey,
  refreshCredential: refreshOAuthCredential,
  readBootstrapCredential: ({ profileId, credential }) => (0, _storeCSOk8Bno._)({
    profileId,
    credential
  }),
  isRefreshTokenReusedError
});
async function tryResolveOAuthProfile(params) {
  const { cfg, store, profileId } = params;
  const cred = store.profiles[profileId];
  if (!cred || cred.type !== "oauth") return null;
  if (!isProfileConfigCompatible({
    cfg,
    profileId,
    provider: cred.provider,
    mode: cred.type
  })) return null;
  const resolved = await oauthManager.resolveOAuthAccess({
    store,
    profileId,
    credential: cred,
    agentDir: params.agentDir,
    cfg
  });
  if (!resolved) return null;
  return buildApiKeyProfileResult({
    apiKey: resolved.apiKey,
    provider: resolved.credential.provider,
    email: resolved.credential.email ?? cred.email
  });
}
async function resolveProfileSecretString(params) {
  let resolvedValue = params.value?.trim();
  if (resolvedValue) {
    const inlineRef = (0, _typesSecretsCL51SR4g.o)(resolvedValue, params.refDefaults);
    if (inlineRef) try {
      resolvedValue = await (0, _resolveCqhiFUTe.i)(inlineRef, {
        config: params.configForRefResolution,
        env: process.env,
        cache: params.cache
      });
    } catch (err) {
      _storeCSOk8Bno.I.debug(params.inlineFailureMessage, {
        profileId: params.profileId,
        provider: params.provider,
        error: (0, _errorsQN8rySzW.i)(err)
      });
    }
  }
  const explicitRef = (0, _typesSecretsCL51SR4g.o)(params.valueRef, params.refDefaults);
  if (!resolvedValue && explicitRef) try {
    resolvedValue = await (0, _resolveCqhiFUTe.i)(explicitRef, {
      config: params.configForRefResolution,
      env: process.env,
      cache: params.cache
    });
  } catch (err) {
    _storeCSOk8Bno.I.debug(params.refFailureMessage, {
      profileId: params.profileId,
      provider: params.provider,
      error: (0, _errorsQN8rySzW.i)(err)
    });
  }
  return resolvedValue;
}
async function resolveApiKeyForProfile(params) {
  const { cfg, store, profileId } = params;
  const cred = store.profiles[profileId];
  if (!cred) return null;
  if (!isProfileConfigCompatible({
    cfg,
    profileId,
    provider: cred.provider,
    mode: cred.type,
    allowOAuthTokenCompatibility: true
  })) return null;
  const refResolveCache = {};
  const configForRefResolution = cfg ?? (0, _ioE69J4lLI.i)();
  const refDefaults = configForRefResolution.secrets?.defaults;
  (0, _policyDJ7xi3jO.t)({
    store,
    cfg: configForRefResolution,
    profileIds: [profileId],
    context: `auth profile ${profileId}`
  });
  if (cred.type === "api_key") {
    const key = await resolveProfileSecretString({
      profileId,
      provider: cred.provider,
      value: cred.key,
      valueRef: cred.keyRef,
      refDefaults,
      configForRefResolution,
      cache: refResolveCache,
      inlineFailureMessage: "failed to resolve inline auth profile api_key ref",
      refFailureMessage: "failed to resolve auth profile api_key ref"
    });
    if (!key) return null;
    return buildApiKeyProfileResult({
      apiKey: key,
      provider: cred.provider,
      email: cred.email
    });
  }
  if (cred.type === "token") {
    const expiryState = (0, _storeCSOk8Bno.D)(cred.expires);
    if (expiryState === "expired" || expiryState === "invalid_expires") return null;
    const token = await resolveProfileSecretString({
      profileId,
      provider: cred.provider,
      value: cred.token,
      valueRef: cred.tokenRef,
      refDefaults,
      configForRefResolution,
      cache: refResolveCache,
      inlineFailureMessage: "failed to resolve inline auth profile token ref",
      refFailureMessage: "failed to resolve auth profile token ref"
    });
    if (!token) return null;
    return buildApiKeyProfileResult({
      apiKey: token,
      provider: cred.provider,
      email: cred.email
    });
  }
  try {
    const resolved = await oauthManager.resolveOAuthAccess({
      store,
      agentDir: params.agentDir,
      profileId,
      credential: cred,
      cfg
    });
    if (!resolved) return null;
    return buildApiKeyProfileResult({
      apiKey: resolved.apiKey,
      provider: resolved.credential.provider,
      email: resolved.credential.email ?? cred.email
    });
  } catch (error) {
    const refreshedStore = error instanceof OAuthManagerRefreshError ? error.getRefreshedStore() : (0, _storeCSOk8Bno.c)(params.agentDir);
    const surfacedCause = error instanceof OAuthManagerRefreshError && error.cause ? error.cause : error;
    const surfacedMessageError = error instanceof OAuthManagerRefreshError && error.code === "refresh_contention" ? error : surfacedCause;
    const fallbackProfileId = (0, _repairBvCst.n)({
      cfg,
      store: refreshedStore,
      provider: cred.provider,
      legacyProfileId: profileId
    });
    if (fallbackProfileId && fallbackProfileId !== profileId) try {
      const fallbackResolved = await tryResolveOAuthProfile({
        cfg,
        store: refreshedStore,
        profileId: fallbackProfileId,
        agentDir: params.agentDir
      });
      if (fallbackResolved) return fallbackResolved;
    } catch {}
    const message = extractErrorMessage(surfacedMessageError);
    const hint = await formatAuthDoctorHint({
      cfg,
      store: refreshedStore,
      provider: cred.provider,
      profileId
    });
    throw new Error(`OAuth token refresh failed for ${cred.provider}: ${message}. Please try again or re-authenticate.` + (hint ? `\n\n${hint}` : ""), { cause: error });
  }
}
//#endregion /* v9-45d45f9e65820107 */
