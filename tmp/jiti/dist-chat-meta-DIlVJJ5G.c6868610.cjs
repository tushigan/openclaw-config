"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = listChatChannels;exports.r = buildChatChannelMetaById;exports.t = getChatChannelMeta;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _idsPHiL43bp = require("./ids-PHiL43bp.js");
var _channelMetaBUHH6hK = require("./channel-meta-BU-HH6hK.js");
//#region src/channels/chat-meta-shared.ts
const CHAT_CHANNEL_ID_SET = new Set(_idsPHiL43bp.n);
function toChatChannelMeta(params) {
  const label = (0, _stringCoerceBje8XVt.c)(params.channel.label);
  if (!label) throw new Error(`Missing label for bundled chat channel "${params.id}"`);
  return (0, _channelMetaBUHH6hK.t)({
    id: params.id,
    channel: params.channel,
    label,
    selectionLabel: (0, _stringCoerceBje8XVt.c)(params.channel.selectionLabel) || label,
    docsPath: (0, _stringCoerceBje8XVt.c)(params.channel.docsPath) || `/channels/${params.id}`,
    docsLabel: (0, _stringCoerceBje8XVt.c)(params.channel.docsLabel),
    blurb: (0, _stringCoerceBje8XVt.c)(params.channel.blurb) || "",
    detailLabel: (0, _stringCoerceBje8XVt.c)(params.channel.detailLabel),
    systemImage: (0, _stringCoerceBje8XVt.c)(params.channel.systemImage),
    arrayFieldMode: "non-empty",
    selectionDocsPrefixMode: "defined"
  });
}
function buildChatChannelMetaById() {
  const entries = /* @__PURE__ */new Map();
  for (const entry of (0, _idsPHiL43bp.i)()) {
    const rawId = (0, _stringCoerceBje8XVt.c)(entry.id);
    if (!rawId || !CHAT_CHANNEL_ID_SET.has(rawId)) continue;
    const id = rawId;
    entries.set(id, toChatChannelMeta({
      id,
      channel: entry.channel
    }));
  }
  return Object.freeze(Object.fromEntries(entries));
}
//#endregion
//#region src/channels/chat-meta.ts
const CHAT_CHANNEL_META = buildChatChannelMetaById();
function listChatChannels() {
  return _idsPHiL43bp.n.map((id) => CHAT_CHANNEL_META[id]);
}
function getChatChannelMeta(id) {
  return CHAT_CHANNEL_META[id];
}
//#endregion /* v9-55dbcfed295cd310 */
