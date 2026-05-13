"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = isInternalNonDeliveryChannel;exports.n = normalizeMessageChannel;exports.r = void 0;exports.t = isDeliverableMessageChannel;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _idsPHiL43bp = require("./ids-PHiL43bp.js");
var _runtimeChannelStateC_dvLbjP = require("./runtime-channel-state-C_dvLbjP.js");
//#region src/utils/message-channel-constants.ts
const INTERNAL_MESSAGE_CHANNEL = exports.r = "webchat";
const INTERNAL_NON_DELIVERY_CHANNELS = [
"heartbeat",
"cron",
"webhook"];

function isInternalNonDeliveryChannel(value) {
  return INTERNAL_NON_DELIVERY_CHANNELS.includes(value);
}
//#endregion
//#region src/channels/registry-normalize.ts
function listRegisteredChannelPluginEntries() {
  const channelRegistry = (0, _runtimeChannelStateC_dvLbjP.t)();
  if (channelRegistry?.channels && channelRegistry.channels.length > 0) return channelRegistry.channels;
  return [];
}
function normalizeAnyChannelId(raw) {
  const key = (0, _stringCoerceBje8XVt.s)(raw);
  if (!key) return null;
  return listRegisteredChannelPluginEntries().find((entry) => {
    const id = (0, _stringCoerceBje8XVt.s)(entry.plugin.id ?? "") ?? "";
    if (id && id === key) return true;
    return (entry.plugin.meta?.aliases ?? []).some((alias) => (0, _stringCoerceBje8XVt.s)(alias) === key);
  })?.plugin.id ?? null;
}
//#endregion
//#region src/utils/message-channel-core.ts
function normalizeMessageChannel(raw) {
  const normalized = (0, _stringCoerceBje8XVt.s)(raw);
  if (!normalized) return;
  if (normalized === "webchat") return INTERNAL_MESSAGE_CHANNEL;
  const builtIn = (0, _idsPHiL43bp.r)(normalized);
  if (builtIn) return builtIn;
  return normalizeAnyChannelId(normalized) ?? normalized;
}
function isDeliverableMessageChannel(value) {
  const normalized = normalizeMessageChannel(value);
  return normalized !== void 0 && normalized !== "webchat" && normalized === value;
}
//#endregion /* v9-f641079958e8c188 */
