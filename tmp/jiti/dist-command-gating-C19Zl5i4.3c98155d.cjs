"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveControlCommandGate;exports.r = resolveDualTextControlCommandGate;exports.t = resolveCommandAuthorizedFromAuthorizers; //#region src/channels/command-gating.ts
function resolveCommandAuthorizedFromAuthorizers(params) {
  const { useAccessGroups, authorizers } = params;
  const mode = params.modeWhenAccessGroupsOff ?? "allow";
  if (!useAccessGroups) {
    if (mode === "allow") return true;
    if (mode === "deny") return false;
    if (!authorizers.some((entry) => entry.configured)) return true;
    return authorizers.some((entry) => entry.configured && entry.allowed);
  }
  return authorizers.some((entry) => entry.configured && entry.allowed);
}
function resolveControlCommandGate(params) {
  const commandAuthorized = resolveCommandAuthorizedFromAuthorizers({
    useAccessGroups: params.useAccessGroups,
    authorizers: params.authorizers,
    modeWhenAccessGroupsOff: params.modeWhenAccessGroupsOff
  });
  return {
    commandAuthorized,
    shouldBlock: params.allowTextCommands && params.hasControlCommand && !commandAuthorized
  };
}
function resolveDualTextControlCommandGate(params) {
  return resolveControlCommandGate({
    useAccessGroups: params.useAccessGroups,
    authorizers: [{
      configured: params.primaryConfigured,
      allowed: params.primaryAllowed
    }, {
      configured: params.secondaryConfigured,
      allowed: params.secondaryAllowed
    }],
    allowTextCommands: true,
    hasControlCommand: params.hasControlCommand,
    modeWhenAccessGroupsOff: params.modeWhenAccessGroupsOff
  });
}
//#endregion /* v9-90bc2142d7ada59d */
