"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveAgentSessionDirsFromAgentsDir;exports.r = resolveAgentSessionDirsFromAgentsDirSync;exports.t = resolveAgentSessionDirs;var _nodeFs = _interopRequireDefault(require("node:fs"));
var _nodePath = _interopRequireDefault(require("node:path"));
var _promises = _interopRequireDefault(require("node:fs/promises"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
//#region src/agents/session-dirs.ts
function mapAgentSessionDirs(agentsDir, entries) {
  return entries.filter((entry) => entry.isDirectory()).map((entry) => _nodePath.default.join(agentsDir, entry.name, "sessions")).toSorted((a, b) => a.localeCompare(b));
}
async function resolveAgentSessionDirsFromAgentsDir(agentsDir) {
  let entries = [];
  try {
    entries = await _promises.default.readdir(agentsDir, { withFileTypes: true });
  } catch (err) {
    if (err.code === "ENOENT") return [];
    throw err;
  }
  return mapAgentSessionDirs(agentsDir, entries);
}
function resolveAgentSessionDirsFromAgentsDirSync(agentsDir) {
  let entries = [];
  try {
    entries = _nodeFs.default.readdirSync(agentsDir, { withFileTypes: true });
  } catch (err) {
    if (err.code === "ENOENT") return [];
    throw err;
  }
  return mapAgentSessionDirs(agentsDir, entries);
}
async function resolveAgentSessionDirs(stateDir) {
  return await resolveAgentSessionDirsFromAgentsDir(_nodePath.default.join(stateDir, "agents"));
}
//#endregion /* v9-5868eb48151e2ab3 */
