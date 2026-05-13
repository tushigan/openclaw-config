"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.n = resolveEffectiveAgentSkillsLimits;exports.t = resolveEffectiveAgentSkillFilter;var _sessionKeyC0K0uhmG = require("./session-key-C0K0uhmG.js");
var _filter5X4NCOQk = require("./filter-5X4NCOQk.js");
//#region src/agents/skills/agent-filter.ts
function resolveAgentEntry(cfg, agentId) {
  if (!cfg) return;
  const normalizedAgentId = (0, _sessionKeyC0K0uhmG.c)(agentId);
  return cfg.agents?.list?.find((entry) => (0, _sessionKeyC0K0uhmG.c)(entry.id) === normalizedAgentId);
}
/**
* Explicit per-agent skills win when present; otherwise fall back to shared defaults.
* Unknown agent ids also fall back to defaults so legacy/unresolved callers do not widen access.
*/
function resolveEffectiveAgentSkillFilter(cfg, agentId) {
  if (!cfg) return;
  const agentEntry = resolveAgentEntry(cfg, agentId);
  if (agentEntry && Object.hasOwn(agentEntry, "skills")) return (0, _filter5X4NCOQk.n)(agentEntry.skills);
  return (0, _filter5X4NCOQk.n)(cfg.agents?.defaults?.skills);
}
function resolveEffectiveAgentSkillsLimits(cfg, agentId) {
  if (!agentId) return;
  const agentEntry = resolveAgentEntry(cfg, agentId);
  if (!agentEntry || !Object.hasOwn(agentEntry, "skillsLimits")) return;
  const { maxSkillsPromptChars } = agentEntry.skillsLimits ?? {};
  return typeof maxSkillsPromptChars === "number" ? { maxSkillsPromptChars } : void 0;
}
//#endregion /* v9-bd2ed8eb7d55a7d4 */
