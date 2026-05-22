"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = buildPairingReply;var _commandFormatUt6bcRZg = require("./command-format-ut6bcRZg.js");
//#region src/pairing/pairing-messages.ts
function buildPairingReply(params) {
  const { channel, idLine, code } = params;
  const approveCommand = (0, _commandFormatUt6bcRZg.t)(`openclaw pairing approve ${channel} ${code}`);
  return [
  "OpenClaw: access not configured.",
  "",
  idLine,
  "Pairing code:",
  "```",
  code,
  "```",
  "",
  "Ask the bot owner to approve with:",
  (0, _commandFormatUt6bcRZg.t)(`openclaw pairing approve ${channel} ${code}`),
  "```",
  approveCommand,
  "```"].
  join("\n");
}
//#endregion /* v9-ad6341d2619ce4e6 */
