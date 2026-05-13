"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = resolveOpenClawAgentDir;var _pathsC1_Y0cDn = require("./paths-C1_Y0cDn.js");
var _utilsD5swhEXt = require("./utils-D5swhEXt.js");
var _sessionKeyC0K0uhmG = require("./session-key-C0K0uhmG.js");
var _nodePath = _interopRequireDefault(require("node:path"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/agents/agent-paths.ts
function resolveOpenClawAgentDir(env = process.env) {
  const override = env.OPENCLAW_AGENT_DIR?.trim() || env.PI_CODING_AGENT_DIR?.trim();
  if (override) return (0, _utilsD5swhEXt.p)(override, env);
  return (0, _utilsD5swhEXt.p)(_nodePath.default.join((0, _pathsC1_Y0cDn.v)(env), "agents", _sessionKeyC0K0uhmG.t, "agent"), env);
}
//#endregion /* v9-09b0115bad4cfa00 */
