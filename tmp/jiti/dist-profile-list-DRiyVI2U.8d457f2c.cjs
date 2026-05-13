"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = listProfilesForProvider;exports.t = dedupeProfileIds;var _providerAuthAliasesChhMyI_u = require("./provider-auth-aliases-ChhMyI_u.js");
//#region src/agents/auth-profiles/profile-list.ts
function dedupeProfileIds(profileIds) {
  return [...new Set(profileIds)];
}
function listProfilesForProvider(store, provider) {
  const providerKey = (0, _providerAuthAliasesChhMyI_u.r)(provider);
  return Object.entries(store.profiles).filter(([, cred]) => (0, _providerAuthAliasesChhMyI_u.r)(cred.provider) === providerKey).map(([id]) => id);
}
//#endregion /* v9-f641306cb5bd2902 */
