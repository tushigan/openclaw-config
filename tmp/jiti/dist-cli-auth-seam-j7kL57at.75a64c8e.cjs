"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = readClaudeCliCredentialsForSetup;exports.r = readClaudeCliCredentialsForSetupNonInteractive;exports.t = readClaudeCliCredentialsForRuntime;var _storeCSOk8Bno = require("./store-CSOk8Bno.js");
require("./provider-auth-Kvk9CJPa.js");
//#region extensions/anthropic/cli-auth-seam.ts
function readClaudeCliCredentialsForSetup() {
  return (0, _storeCSOk8Bno.O)();
}
function readClaudeCliCredentialsForSetupNonInteractive() {
  return (0, _storeCSOk8Bno.O)({ allowKeychainPrompt: false });
}
function readClaudeCliCredentialsForRuntime() {
  return (0, _storeCSOk8Bno.O)({ allowKeychainPrompt: false });
}
//#endregion /* v9-c9f00729ca486951 */
