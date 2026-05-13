"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _cliAuthSeamJ7kL57at = require("../../cli-auth-seam-j7kL57at.js");
//#region extensions/anthropic/provider-discovery.ts
const CLAUDE_CLI_BACKEND_ID = "claude-cli";
function resolveClaudeCliSyntheticAuth() {
  const credential = (0, _cliAuthSeamJ7kL57at.t)();
  if (!credential) return;
  return credential.type === "oauth" ? {
    apiKey: credential.access,
    source: "Claude CLI native auth",
    mode: "oauth",
    expiresAt: credential.expires
  } : {
    apiKey: credential.token,
    source: "Claude CLI native auth",
    mode: "token",
    expiresAt: credential.expires
  };
}
const anthropicProviderDiscovery = exports.default = {
  id: CLAUDE_CLI_BACKEND_ID,
  label: "Claude CLI",
  docsPath: "/providers/models",
  auth: [],
  resolveSyntheticAuth: ({ provider }) => provider === CLAUDE_CLI_BACKEND_ID ? resolveClaudeCliSyntheticAuth() : void 0
};
//#endregion /* v9-70216848b66a7b8d */
