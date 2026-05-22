"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = formatSetExplicitDefaultInstruction;exports.r = formatSetExplicitDefaultToConfiguredInstruction;exports.t = formatChannelAccountsDefaultPath; //#region src/routing/default-account-warnings.ts
function formatChannelDefaultAccountPath(channelKey) {
  return `channels.${channelKey}.defaultAccount`;
}
function formatChannelAccountsDefaultPath(channelKey) {
  return `channels.${channelKey}.accounts.default`;
}
function formatSetExplicitDefaultInstruction(channelKey) {
  return `Set ${formatChannelDefaultAccountPath(channelKey)} or add ${formatChannelAccountsDefaultPath(channelKey)}`;
}
function formatSetExplicitDefaultToConfiguredInstruction(params) {
  return `Set ${formatChannelDefaultAccountPath(params.channelKey)} to one of these accounts, or add ${formatChannelAccountsDefaultPath(params.channelKey)}`;
}
//#endregion /* v9-8745a0330af14043 */
