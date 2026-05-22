"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = normalizeConversationText;exports.n = normalizeConversationRef;exports.r = normalizeConversationTargetRef;exports.t = buildChannelAccountKey;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _accountIdBj7l9NI = require("./account-id-Bj7l9NI7.js");
//#region src/acp/conversation-id.ts
function normalizeConversationText(value) {
  if (typeof value === "string") return value.trim();
  if (typeof value === "number" || typeof value === "bigint" || typeof value === "boolean") return `${value}`.trim();
  return "";
}
//#endregion
//#region src/infra/outbound/session-binding-normalization.ts
function normalizeConversationTargetRef(ref) {
  const conversationId = (0, _stringCoerceBje8XVt.c)(ref.conversationId) ?? "";
  const parentConversationId = (0, _stringCoerceBje8XVt.c)(ref.parentConversationId);
  const { parentConversationId: _ignoredParentConversationId, ...rest } = ref;
  return {
    ...rest,
    conversationId,
    ...(parentConversationId && parentConversationId !== conversationId ? { parentConversationId } : {})
  };
}
function normalizeConversationRef(ref) {
  return {
    ...normalizeConversationTargetRef(ref),
    channel: (0, _stringCoerceBje8XVt.a)(ref.channel),
    accountId: (0, _accountIdBj7l9NI.n)(ref.accountId)
  };
}
function buildChannelAccountKey(params) {
  return `${(0, _stringCoerceBje8XVt.a)(params.channel)}:${(0, _accountIdBj7l9NI.n)(params.accountId)}`;
}
//#endregion /* v9-1f87f19fecc5e9e9 */
