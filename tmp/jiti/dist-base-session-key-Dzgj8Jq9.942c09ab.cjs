"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = buildOutboundBaseSessionKey;var _resolveRouteBNuWCNW = require("./resolve-route-BNuWCNW8.js");
//#region src/infra/outbound/base-session-key.ts
function buildOutboundBaseSessionKey(params) {
  return (0, _resolveRouteBNuWCNW.t)({
    agentId: params.agentId,
    channel: params.channel,
    accountId: params.accountId,
    peer: params.peer,
    dmScope: params.cfg.session?.dmScope ?? "main",
    identityLinks: params.cfg.session?.identityLinks
  });
}
//#endregion /* v9-7ea0fe40ec5f728b */
