"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = resolveDmGroupAccessWithCommandGate;exports.c = resolveOpenDmAllowlistAccess;exports.i = resolveDmGroupAccessDecision;exports.l = resolvePinnedMainDmOwnerFromAllowlist;exports.n = readStoreAllowFromForDmPolicy;exports.o = resolveDmGroupAccessWithLists;exports.r = resolveDmAllowState;exports.s = resolveEffectiveAllowFromLists;exports.t = void 0;var _stringNormalizationC5SGsaST = require("./string-normalization-C5SGsaST.js");
var _commandGatingC19Zl5i = require("./command-gating-C19Zl5i4.js");
var _pairingStoreC3tDeLw = require("./pairing-store-C3tDe-Lw.js");
var _allowFromBDAbxTrK = require("./allow-from-BDAbxTrK.js");
var _groupAccessDdKWV2ji = require("./group-access-DdKWV2ji.js");
//#region src/security/dm-policy-shared.ts
function resolvePinnedMainDmOwnerFromAllowlist(params) {
  if ((params.dmScope ?? "main") !== "main") return null;
  const rawAllowFrom = Array.isArray(params.allowFrom) ? params.allowFrom : [];
  if (rawAllowFrom.some((entry) => String(entry).trim() === "*")) return null;
  const normalizedOwners = Array.from(new Set(rawAllowFrom.map((entry) => params.normalizeEntry(String(entry))).filter((entry) => Boolean(entry))));
  return normalizedOwners.length === 1 ? normalizedOwners[0] : null;
}
function resolveEffectiveAllowFromLists(params) {
  const allowFrom = Array.isArray(params.allowFrom) ? params.allowFrom : void 0;
  const groupAllowFrom = Array.isArray(params.groupAllowFrom) ? params.groupAllowFrom : void 0;
  return {
    effectiveAllowFrom: (0, _stringNormalizationC5SGsaST.s)((0, _allowFromBDAbxTrK.r)({
      allowFrom,
      storeAllowFrom: Array.isArray(params.storeAllowFrom) ? params.storeAllowFrom : void 0,
      dmPolicy: params.dmPolicy ?? void 0
    })),
    effectiveGroupAllowFrom: (0, _stringNormalizationC5SGsaST.s)((0, _allowFromBDAbxTrK.i)({
      allowFrom,
      groupAllowFrom,
      fallbackToAllowFrom: params.groupAllowFromFallbackToAllowFrom ?? void 0
    }))
  };
}
const DM_GROUP_ACCESS_REASON = exports.t = {
  GROUP_POLICY_ALLOWED: "group_policy_allowed",
  GROUP_POLICY_DISABLED: "group_policy_disabled",
  GROUP_POLICY_EMPTY_ALLOWLIST: "group_policy_empty_allowlist",
  GROUP_POLICY_NOT_ALLOWLISTED: "group_policy_not_allowlisted",
  DM_POLICY_OPEN: "dm_policy_open",
  DM_POLICY_DISABLED: "dm_policy_disabled",
  DM_POLICY_ALLOWLISTED: "dm_policy_allowlisted",
  DM_POLICY_PAIRING_REQUIRED: "dm_policy_pairing_required",
  DM_POLICY_NOT_ALLOWLISTED: "dm_policy_not_allowlisted"
};
function resolveOpenDmAllowlistAccess(params) {
  const effectiveAllowFrom = (0, _stringNormalizationC5SGsaST.s)(params.effectiveAllowFrom);
  if (effectiveAllowFrom.includes("*")) return {
    decision: "allow",
    reasonCode: DM_GROUP_ACCESS_REASON.DM_POLICY_OPEN,
    reason: "dmPolicy=open"
  };
  if (params.isSenderAllowed(effectiveAllowFrom)) return {
    decision: "allow",
    reasonCode: DM_GROUP_ACCESS_REASON.DM_POLICY_ALLOWLISTED,
    reason: "dmPolicy=open (allowlisted)"
  };
  return {
    decision: "block",
    reasonCode: DM_GROUP_ACCESS_REASON.DM_POLICY_NOT_ALLOWLISTED,
    reason: "dmPolicy=open (not allowlisted)"
  };
}
async function readStoreAllowFromForDmPolicy(params) {
  if (params.shouldRead === false || params.dmPolicy === "allowlist" || params.dmPolicy === "open") return [];
  return await (params.readStore ?? ((provider, accountId) => (0, _pairingStoreC3tDeLw.a)(provider, process.env, accountId)))(params.provider, params.accountId).catch(() => []);
}
function resolveDmGroupAccessDecision(params) {
  const dmPolicy = params.dmPolicy ?? "pairing";
  const groupPolicy = params.groupPolicy === "open" || params.groupPolicy === "disabled" ? params.groupPolicy : "allowlist";
  const effectiveAllowFrom = (0, _stringNormalizationC5SGsaST.s)(params.effectiveAllowFrom);
  const effectiveGroupAllowFrom = (0, _stringNormalizationC5SGsaST.s)(params.effectiveGroupAllowFrom);
  if (params.isGroup) {
    const groupAccess = (0, _groupAccessDdKWV2ji.n)({
      groupPolicy,
      allowlistConfigured: effectiveGroupAllowFrom.length > 0,
      allowlistMatched: params.isSenderAllowed(effectiveGroupAllowFrom)
    });
    if (!groupAccess.allowed) {
      if (groupAccess.reason === "disabled") return {
        decision: "block",
        reasonCode: DM_GROUP_ACCESS_REASON.GROUP_POLICY_DISABLED,
        reason: "groupPolicy=disabled"
      };
      if (groupAccess.reason === "empty_allowlist") return {
        decision: "block",
        reasonCode: DM_GROUP_ACCESS_REASON.GROUP_POLICY_EMPTY_ALLOWLIST,
        reason: "groupPolicy=allowlist (empty allowlist)"
      };
      if (groupAccess.reason === "not_allowlisted") return {
        decision: "block",
        reasonCode: DM_GROUP_ACCESS_REASON.GROUP_POLICY_NOT_ALLOWLISTED,
        reason: "groupPolicy=allowlist (not allowlisted)"
      };
    }
    return {
      decision: "allow",
      reasonCode: DM_GROUP_ACCESS_REASON.GROUP_POLICY_ALLOWED,
      reason: `groupPolicy=${groupPolicy}`
    };
  }
  if (dmPolicy === "disabled") return {
    decision: "block",
    reasonCode: DM_GROUP_ACCESS_REASON.DM_POLICY_DISABLED,
    reason: "dmPolicy=disabled"
  };
  if (dmPolicy === "open") return resolveOpenDmAllowlistAccess({
    effectiveAllowFrom,
    isSenderAllowed: params.isSenderAllowed
  });
  if (params.isSenderAllowed(effectiveAllowFrom)) return {
    decision: "allow",
    reasonCode: DM_GROUP_ACCESS_REASON.DM_POLICY_ALLOWLISTED,
    reason: `dmPolicy=${dmPolicy} (allowlisted)`
  };
  if (dmPolicy === "pairing") return {
    decision: "pairing",
    reasonCode: DM_GROUP_ACCESS_REASON.DM_POLICY_PAIRING_REQUIRED,
    reason: "dmPolicy=pairing (not allowlisted)"
  };
  return {
    decision: "block",
    reasonCode: DM_GROUP_ACCESS_REASON.DM_POLICY_NOT_ALLOWLISTED,
    reason: `dmPolicy=${dmPolicy} (not allowlisted)`
  };
}
function resolveDmGroupAccessWithLists(params) {
  const { effectiveAllowFrom, effectiveGroupAllowFrom } = resolveEffectiveAllowFromLists({
    allowFrom: params.allowFrom,
    groupAllowFrom: params.groupAllowFrom,
    storeAllowFrom: params.storeAllowFrom,
    dmPolicy: params.dmPolicy,
    groupAllowFromFallbackToAllowFrom: params.groupAllowFromFallbackToAllowFrom
  });
  return {
    ...resolveDmGroupAccessDecision({
      isGroup: params.isGroup,
      dmPolicy: params.dmPolicy,
      groupPolicy: params.groupPolicy,
      effectiveAllowFrom,
      effectiveGroupAllowFrom,
      isSenderAllowed: params.isSenderAllowed
    }),
    effectiveAllowFrom,
    effectiveGroupAllowFrom
  };
}
function resolveDmGroupAccessWithCommandGate(params) {
  const access = resolveDmGroupAccessWithLists({
    isGroup: params.isGroup,
    dmPolicy: params.dmPolicy,
    groupPolicy: params.groupPolicy,
    allowFrom: params.allowFrom,
    groupAllowFrom: params.groupAllowFrom,
    storeAllowFrom: params.storeAllowFrom,
    groupAllowFromFallbackToAllowFrom: params.groupAllowFromFallbackToAllowFrom,
    isSenderAllowed: params.isSenderAllowed
  });
  const configuredAllowFrom = (0, _stringNormalizationC5SGsaST.s)(params.allowFrom ?? []);
  const configuredGroupAllowFrom = (0, _stringNormalizationC5SGsaST.s)((0, _allowFromBDAbxTrK.i)({
    allowFrom: configuredAllowFrom,
    groupAllowFrom: (0, _stringNormalizationC5SGsaST.s)(params.groupAllowFrom ?? []),
    fallbackToAllowFrom: params.groupAllowFromFallbackToAllowFrom ?? void 0
  }));
  const commandDmAllowFrom = params.isGroup ? configuredAllowFrom : access.effectiveAllowFrom;
  const commandGroupAllowFrom = params.isGroup ? configuredGroupAllowFrom : access.effectiveGroupAllowFrom;
  const ownerAllowedForCommands = params.isSenderAllowed(commandDmAllowFrom);
  const groupAllowedForCommands = params.isSenderAllowed(commandGroupAllowFrom);
  const commandGate = params.command ? (0, _commandGatingC19Zl5i.n)({
    useAccessGroups: params.command.useAccessGroups,
    authorizers: [{
      configured: commandDmAllowFrom.length > 0,
      allowed: ownerAllowedForCommands
    }, {
      configured: commandGroupAllowFrom.length > 0,
      allowed: groupAllowedForCommands
    }],
    allowTextCommands: params.command.allowTextCommands,
    hasControlCommand: params.command.hasControlCommand
  }) : {
    commandAuthorized: false,
    shouldBlock: false
  };
  return {
    ...access,
    commandAuthorized: commandGate.commandAuthorized,
    shouldBlockControlCommand: params.isGroup && commandGate.shouldBlock
  };
}
async function resolveDmAllowState(params) {
  const configAllowFrom = (0, _stringNormalizationC5SGsaST.s)(Array.isArray(params.allowFrom) ? params.allowFrom : void 0);
  const hasWildcard = configAllowFrom.includes("*");
  const storeAllowFrom = await readStoreAllowFromForDmPolicy({
    provider: params.provider,
    accountId: params.accountId,
    dmPolicy: params.dmPolicy,
    readStore: params.readStore
  });
  const normalizeEntry = params.normalizeEntry ?? ((value) => value);
  const normalizedCfg = configAllowFrom.filter((value) => value !== "*").map((value) => normalizeEntry(value)).map((value) => value.trim()).filter(Boolean);
  const normalizedStore = storeAllowFrom.map((value) => normalizeEntry(value)).map((value) => value.trim()).filter(Boolean);
  const allowCount = new Set([...normalizedCfg, ...normalizedStore]).size;
  return {
    configAllowFrom,
    hasWildcard,
    allowCount,
    isMultiUserDm: hasWildcard || allowCount > 1
  };
}
//#endregion /* v9-a4ae87cc2c565507 */
