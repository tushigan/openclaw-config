"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = suggestOAuthProfileIdForLegacyDefault;exports.t = repairOAuthProfileIdMismatch;var _providerIdDIRgKpoh = require("./provider-id-DIRgKpoh.js");
var _identityCMUYJwmU = require("./identity-CMUYJwmU.js");
var _profileListDRiyVI2U = require("./profile-list-DRiyVI2U.js");
//#region src/agents/auth-profiles/repair.ts
function getProfileSuffix(profileId) {
  const idx = profileId.indexOf(":");
  if (idx < 0) return "";
  return profileId.slice(idx + 1);
}
function isEmailLike(value) {
  const trimmed = value.trim();
  if (!trimmed) return false;
  return trimmed.includes("@") && trimmed.includes(".");
}
function suggestOAuthProfileIdForLegacyDefault(params) {
  const providerKey = (0, _providerIdDIRgKpoh.r)(params.provider);
  if (getProfileSuffix(params.legacyProfileId) !== "default") return null;
  const legacyCfg = params.cfg?.auth?.profiles?.[params.legacyProfileId];
  if (legacyCfg && (0, _providerIdDIRgKpoh.r)(legacyCfg.provider) === providerKey && legacyCfg.mode !== "oauth") return null;
  const oauthProfiles = (0, _profileListDRiyVI2U.n)(params.store, providerKey).filter((id) => params.store.profiles[id]?.type === "oauth");
  if (oauthProfiles.length === 0) return null;
  const configuredEmail = legacyCfg?.email?.trim();
  if (configuredEmail) {
    const byEmail = oauthProfiles.find((id) => {
      return (0, _identityCMUYJwmU.n)({
        cfg: params.cfg,
        store: params.store,
        profileId: id
      }).email === configuredEmail || id === `${providerKey}:${configuredEmail}`;
    });
    if (byEmail) return byEmail;
  }
  const lastGood = params.store.lastGood?.[providerKey] ?? params.store.lastGood?.[params.provider];
  if (lastGood && oauthProfiles.includes(lastGood)) return lastGood;
  const nonLegacy = oauthProfiles.filter((id) => id !== params.legacyProfileId);
  if (nonLegacy.length === 1) return nonLegacy[0] ?? null;
  const emailLike = nonLegacy.filter((id) => isEmailLike(getProfileSuffix(id)));
  if (emailLike.length === 1) return emailLike[0] ?? null;
  return null;
}
function repairOAuthProfileIdMismatch(params) {
  const legacyProfileId = params.legacyProfileId ?? `${(0, _providerIdDIRgKpoh.r)(params.provider)}:default`;
  const legacyCfg = params.cfg.auth?.profiles?.[legacyProfileId];
  if (!legacyCfg) return {
    config: params.cfg,
    changes: [],
    migrated: false
  };
  if (legacyCfg.mode !== "oauth") return {
    config: params.cfg,
    changes: [],
    migrated: false
  };
  if ((0, _providerIdDIRgKpoh.r)(legacyCfg.provider) !== (0, _providerIdDIRgKpoh.r)(params.provider)) return {
    config: params.cfg,
    changes: [],
    migrated: false
  };
  const toProfileId = suggestOAuthProfileIdForLegacyDefault({
    cfg: params.cfg,
    store: params.store,
    provider: params.provider,
    legacyProfileId
  });
  if (!toProfileId || toProfileId === legacyProfileId) return {
    config: params.cfg,
    changes: [],
    migrated: false
  };
  const { email: toEmail, displayName: toDisplayName } = (0, _identityCMUYJwmU.n)({
    store: params.store,
    profileId: toProfileId
  });
  const { email: _legacyEmail, displayName: _legacyDisplayName, ...legacyCfgRest } = legacyCfg;
  const nextProfiles = { ...params.cfg.auth?.profiles };
  delete nextProfiles[legacyProfileId];
  nextProfiles[toProfileId] = {
    ...legacyCfgRest,
    ...(toDisplayName ? { displayName: toDisplayName } : {}),
    ...(toEmail ? { email: toEmail } : {})
  };
  const providerKey = (0, _providerIdDIRgKpoh.r)(params.provider);
  const nextOrder = (() => {
    const order = params.cfg.auth?.order;
    if (!order) return;
    const resolvedKey = (0, _providerIdDIRgKpoh.t)(order, providerKey);
    if (!resolvedKey) return order;
    const existing = order[resolvedKey];
    if (!Array.isArray(existing)) return order;
    const deduped = (0, _profileListDRiyVI2U.t)(existing.map((id) => id === legacyProfileId ? toProfileId : id).filter((id) => typeof id === "string" && id.trim().length > 0));
    return {
      ...order,
      [resolvedKey]: deduped
    };
  })();
  return {
    config: {
      ...params.cfg,
      auth: {
        ...params.cfg.auth,
        profiles: nextProfiles,
        ...(nextOrder ? { order: nextOrder } : {})
      }
    },
    changes: [`Auth: migrate ${legacyProfileId} → ${toProfileId} (OAuth profile id)`],
    migrated: true,
    fromProfileId: legacyProfileId,
    toProfileId
  };
}
//#endregion /* v9-53ad0c764976e403 */
