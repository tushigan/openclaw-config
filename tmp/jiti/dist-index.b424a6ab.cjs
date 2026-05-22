"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _subagentHooksApi = require("./subagent-hooks-api.js");
var _channelEntryContract = require("openclaw/plugin-sdk/channel-entry-contract");
//#region extensions/feishu/index.ts
function registerFeishuDocTools(api) {
  (0, _channelEntryContract.loadBundledEntryExportSync)("file:///Users/a123/.openclaw/npm/node_modules/@openclaw/feishu/dist/index.js", {
    specifier: "./api.js",
    exportName: "registerFeishuDocTools"
  })(api);
}
function registerFeishuChatTools(api) {
  (0, _channelEntryContract.loadBundledEntryExportSync)("file:///Users/a123/.openclaw/npm/node_modules/@openclaw/feishu/dist/index.js", {
    specifier: "./api.js",
    exportName: "registerFeishuChatTools"
  })(api);
}
function registerFeishuWikiTools(api) {
  (0, _channelEntryContract.loadBundledEntryExportSync)("file:///Users/a123/.openclaw/npm/node_modules/@openclaw/feishu/dist/index.js", {
    specifier: "./api.js",
    exportName: "registerFeishuWikiTools"
  })(api);
}
function registerFeishuDriveTools(api) {
  (0, _channelEntryContract.loadBundledEntryExportSync)("file:///Users/a123/.openclaw/npm/node_modules/@openclaw/feishu/dist/index.js", {
    specifier: "./api.js",
    exportName: "registerFeishuDriveTools"
  })(api);
}
function registerFeishuPermTools(api) {
  (0, _channelEntryContract.loadBundledEntryExportSync)("file:///Users/a123/.openclaw/npm/node_modules/@openclaw/feishu/dist/index.js", {
    specifier: "./api.js",
    exportName: "registerFeishuPermTools"
  })(api);
}
function registerFeishuBitableTools(api) {
  (0, _channelEntryContract.loadBundledEntryExportSync)("file:///Users/a123/.openclaw/npm/node_modules/@openclaw/feishu/dist/index.js", {
    specifier: "./api.js",
    exportName: "registerFeishuBitableTools"
  })(api);
}
var feishu_default = exports.default = (0, _channelEntryContract.defineBundledChannelEntry)({
  id: "feishu",
  name: "Feishu",
  description: "Feishu/Lark channel plugin",
  importMetaUrl: "file:///Users/a123/.openclaw/npm/node_modules/@openclaw/feishu/dist/index.js",
  plugin: {
    specifier: "./channel-plugin-api.js",
    exportName: "feishuPlugin"
  },
  secrets: {
    specifier: "./secret-contract-api.js",
    exportName: "channelSecrets"
  },
  runtime: {
    specifier: "./runtime-api.js",
    exportName: "setFeishuRuntime"
  },
  registerFull(api) {
    (0, _subagentHooksApi.registerFeishuSubagentHooks)(api);
    registerFeishuDocTools(api);
    registerFeishuChatTools(api);
    registerFeishuWikiTools(api);
    registerFeishuDriveTools(api);
    registerFeishuPermTools(api);
    registerFeishuBitableTools(api);
  }
});
//#endregion /* v9-e36b44c171caac02 */
