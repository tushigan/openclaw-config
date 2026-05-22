"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = issuePairingChallenge;var _pairingMessagesOs97WTVG = require("./pairing-messages-os97WTVG.js");
//#region src/pairing/pairing-challenge.ts
/**
* Shared pairing challenge issuance for DM pairing policy pathways.
* Ensures every channel follows the same create-if-missing + reply flow.
*/
async function issuePairingChallenge(params) {
  const { code, created } = await params.upsertPairingRequest({
    id: params.senderId,
    meta: params.meta
  });
  if (!created) return { created: false };
  params.onCreated?.({ code });
  const replyText = params.buildReplyText?.({
    code,
    senderIdLine: params.senderIdLine
  }) ?? (0, _pairingMessagesOs97WTVG.t)({
    channel: params.channel,
    idLine: params.senderIdLine,
    code
  });
  try {
    await params.sendPairingReply(replyText);
  } catch (err) {
    params.onReplyError?.(err);
  }
  return {
    created: true,
    code
  };
}
//#endregion /* v9-86fb6e3e101c4cb6 */
