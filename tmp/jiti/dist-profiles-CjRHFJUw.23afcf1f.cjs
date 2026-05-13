"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = upsertAuthProfile;exports.i = setAuthProfileOrder;exports.n = promoteAuthProfileInOrder;exports.o = upsertAuthProfileWithLock;exports.r = removeProviderAuthProfilesWithLock;exports.t = markAuthProfileGood;var _stringNormalizationC5SGsaST = require("./string-normalization-C5SGsaST.js");
var _providerIdDIRgKpoh = require("./provider-id-DIRgKpoh.js");
var _providerAuthAliasesChhMyI_u = require("./provider-auth-aliases-ChhMyI_u.js");
var _storeCSOk8Bno = require("./store-CSOk8Bno.js");
var _normalizeSecretInputG30DI_5w = require("./normalize-secret-input-G30DI_5w.js");
var _profileListDRiyVI2U = require("./profile-list-DRiyVI2U.js");
//#region src/agents/auth-profiles/profiles.ts
async function setAuthProfileOrder(params) {
  const providerKey = (0, _providerIdDIRgKpoh.r)(params.provider);
  const deduped = (0, _profileListDRiyVI2U.t)(params.order && Array.isArray(params.order) ? (0, _stringNormalizationC5SGsaST.s)(params.order) : []);
  return await (0, _storeCSOk8Bno.p)({
    agentDir: params.agentDir,
    updater: (store) => {
      store.order = store.order ?? {};
      if (deduped.length === 0) {
        if (!store.order[providerKey]) return false;
        delete store.order[providerKey];
        if (Object.keys(store.order).length === 0) store.order = void 0;
        return true;
      }
      store.order[providerKey] = deduped;
      return true;
    }
  });
}
async function promoteAuthProfileInOrder(params) {
  const providerKey = (0, _providerAuthAliasesChhMyI_u.r)(params.provider);
  return await (0, _storeCSOk8Bno.p)({
    agentDir: params.agentDir,
    updater: (store) => {
      const profile = store.profiles[params.profileId];
      if (!profile || (0, _providerAuthAliasesChhMyI_u.r)(profile.provider) !== providerKey) return false;
      const orderKey = (0, _providerIdDIRgKpoh.t)(store.order, providerKey) ?? (0, _providerIdDIRgKpoh.r)(providerKey);
      const existing = store.order?.[orderKey];
      if (!existing || existing.length === 0) return false;
      const next = (0, _profileListDRiyVI2U.t)([params.profileId, ...existing.filter((profileId) => profileId !== params.profileId)]);
      if (next.length === existing.length && next.every((profileId, idx) => profileId === existing[idx])) return false;
      store.order = {
        ...store.order,
        [orderKey]: next
      };
      return true;
    }
  });
}
function upsertAuthProfile(params) {
  const credential = params.credential.type === "api_key" ? {
    ...params.credential,
    ...(typeof params.credential.key === "string" ? { key: (0, _normalizeSecretInputG30DI_5w.n)(params.credential.key) } : {})
  } : params.credential.type === "token" ? {
    ...params.credential,
    token: (0, _normalizeSecretInputG30DI_5w.n)(params.credential.token)
  } : params.credential;
  const store = (0, _storeCSOk8Bno.r)(params.agentDir);
  store.profiles[params.profileId] = credential;
  (0, _storeCSOk8Bno.f)(store, params.agentDir, {
    filterExternalAuthProfiles: false,
    syncExternalCli: false
  });
}
async function upsertAuthProfileWithLock(params) {
  return await (0, _storeCSOk8Bno.p)({
    agentDir: params.agentDir,
    updater: (store) => {
      store.profiles[params.profileId] = params.credential;
      return true;
    }
  });
}
async function removeProviderAuthProfilesWithLock(params) {
  const providerKey = (0, _providerAuthAliasesChhMyI_u.r)(params.provider);
  const storeOrderKey = (0, _providerIdDIRgKpoh.r)(params.provider);
  return await (0, _storeCSOk8Bno.p)({
    agentDir: params.agentDir,
    updater: (store) => {
      const profileIds = (0, _profileListDRiyVI2U.n)(store, params.provider);
      let changed = false;
      for (const profileId of profileIds) {
        if (store.profiles[profileId]) {
          delete store.profiles[profileId];
          changed = true;
        }
        if (store.usageStats?.[profileId]) {
          delete store.usageStats[profileId];
          changed = true;
        }
      }
      if (store.order?.[storeOrderKey]) {
        delete store.order[storeOrderKey];
        changed = true;
        if (Object.keys(store.order).length === 0) store.order = void 0;
      }
      if (store.lastGood?.[providerKey]) {
        delete store.lastGood[providerKey];
        changed = true;
        if (Object.keys(store.lastGood).length === 0) store.lastGood = void 0;
      }
      if (store.usageStats && Object.keys(store.usageStats).length === 0) store.usageStats = void 0;
      return changed;
    }
  });
}
async function markAuthProfileGood(params) {
  const { store, provider, profileId, agentDir } = params;
  const providerKey = (0, _providerAuthAliasesChhMyI_u.r)(provider);
  const updated = await (0, _storeCSOk8Bno.p)({
    agentDir,
    updater: (freshStore) => {
      const profile = freshStore.profiles[profileId];
      if (!profile || (0, _providerAuthAliasesChhMyI_u.r)(profile.provider) !== providerKey) return false;
      freshStore.lastGood = {
        ...freshStore.lastGood,
        [providerKey]: profileId
      };
      return true;
    }
  });
  if (updated) {
    store.lastGood = updated.lastGood;
    return;
  }
  const profile = store.profiles[profileId];
  if (!profile || (0, _providerAuthAliasesChhMyI_u.r)(profile.provider) !== providerKey) return;
  store.lastGood = {
    ...store.lastGood,
    [providerKey]: profileId
  };
  (0, _storeCSOk8Bno.f)(store, agentDir);
}
//#endregion /* v9-92a317c8304c7d9a */
