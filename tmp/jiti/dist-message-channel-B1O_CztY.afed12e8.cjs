"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = isOperatorUiClient;exports.c = isGatewayMessageChannel;exports.d = resolveGatewayMessageChannel;exports.f = resolveMessageChannel;exports.i = isMarkdownCapableMessageChannel;exports.l = void 0;exports.n = isGatewayCliClient;exports.o = isWebchatClient;exports.r = isInternalMessageChannel;exports.s = isDeliverableMessageChannel;exports.t = isBrowserOperatorUiClient;exports.u = normalizeMessageChannel;var _idsPHiL43bp = require("./ids-PHiL43bp.js");
var _chatMetaDIlVJJ5G = require("./chat-meta-DIlVJJ5G.js");
var _registryBy_qtZ6R = require("./registry-By_qtZ6R.js");
var _clientInfoDQju26jn = require("./client-info-DQju26jn.js");
var _messageChannelCoreD2XbUpib = require("./message-channel-core-D2XbUpib.js");
//#region src/utils/message-channel-normalize.ts
function normalizeMessageChannel(raw) {
  return (0, _messageChannelCoreD2XbUpib.n)(raw);
}
const listPluginChannelIds = () => {
  return (0, _registryBy_qtZ6R.i)();
};
const listDeliverableMessageChannels = () => Array.from(new Set([..._idsPHiL43bp.t, ...listPluginChannelIds()]));exports.l = listDeliverableMessageChannels;
const listGatewayMessageChannels = () => [...listDeliverableMessageChannels(), _messageChannelCoreD2XbUpib.r];
function isGatewayMessageChannel(value) {
  return listGatewayMessageChannels().includes(value);
}
function isDeliverableMessageChannel(value) {
  return listDeliverableMessageChannels().includes(value);
}
function resolveGatewayMessageChannel(raw) {
  const normalized = normalizeMessageChannel(raw);
  if (!normalized) return;
  return isGatewayMessageChannel(normalized) ? normalized : void 0;
}
function resolveMessageChannel(primary, fallback) {
  return normalizeMessageChannel(primary) ?? normalizeMessageChannel(fallback);
}
//#endregion
//#region src/utils/message-channel.ts
function isGatewayCliClient(client) {
  return (0, _clientInfoDQju26jn.s)(client?.mode) === _clientInfoDQju26jn.r.CLI;
}
function isOperatorUiClient(client) {
  const clientId = (0, _clientInfoDQju26jn.c)(client?.id);
  return clientId === _clientInfoDQju26jn.i.CONTROL_UI || clientId === _clientInfoDQju26jn.i.TUI;
}
function isBrowserOperatorUiClient(client) {
  return (0, _clientInfoDQju26jn.c)(client?.id) === _clientInfoDQju26jn.i.CONTROL_UI;
}
function isInternalMessageChannel(raw) {
  return normalizeMessageChannel(raw) === _messageChannelCoreD2XbUpib.r;
}
function isWebchatClient(client) {
  if ((0, _clientInfoDQju26jn.s)(client?.mode) === _clientInfoDQju26jn.r.WEBCHAT) return true;
  return (0, _clientInfoDQju26jn.c)(client?.id) === _clientInfoDQju26jn.i.WEBCHAT_UI;
}
function isMarkdownCapableMessageChannel(raw) {
  const channel = normalizeMessageChannel(raw);
  if (!channel) return false;
  if (channel === "webchat" || channel === "tui") return true;
  const builtInChannel = (0, _idsPHiL43bp.r)(channel);
  if (builtInChannel) return (0, _chatMetaDIlVJJ5G.t)(builtInChannel).markdownCapable === true;
  return (0, _registryBy_qtZ6R.r)(channel)?.markdownCapable === true;
}
//#endregion /* v9-4139faf2fb850173 */
