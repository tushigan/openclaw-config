"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = resolveMainSessionKey;exports.n = resolveAgentMainSessionKey;exports.r = resolveExplicitAgentSessionKey;exports.t = canonicalizeMainSessionAlias;var _sessionKeyC0K0uhmG = require("./session-key-C0K0uhmG.js");
//#region src/config/sessions/main-session.ts
const FALLBACK_DEFAULT_AGENT_ID = "main";
function buildMainSessionKey(agentId, mainKey) {
  return `agent:${(0, _sessionKeyC0K0uhmG.c)(agentId)}:${(0, _sessionKeyC0K0uhmG.l)(mainKey)}`;
}
function resolveMainSessionKey(cfg) {
  if (cfg?.session?.scope === "global") return "global";
  const agents = cfg?.agents?.list ?? [];
  return buildMainSessionKey(agents.find((agent) => agent?.default)?.id ?? agents[0]?.id ?? FALLBACK_DEFAULT_AGENT_ID, cfg?.session?.mainKey);
}
function resolveAgentMainSessionKey(params) {
  return buildMainSessionKey(params.agentId, params.cfg?.session?.mainKey);
}
function resolveExplicitAgentSessionKey(params) {
  const agentId = params.agentId?.trim();
  if (!agentId) return;
  return resolveAgentMainSessionKey({
    cfg: params.cfg,
    agentId
  });
}
function canonicalizeMainSessionAlias(params) {
  const raw = params.sessionKey.trim();
  if (!raw) return raw;
  const agentId = (0, _sessionKeyC0K0uhmG.c)(params.agentId);
  const mainKey = (0, _sessionKeyC0K0uhmG.l)(params.cfg?.session?.mainKey);
  const agentMainSessionKey = buildMainSessionKey(agentId, mainKey);
  const agentMainAliasKey = buildMainSessionKey(agentId, "main");
  const legacyMainKey = buildMainSessionKey(FALLBACK_DEFAULT_AGENT_ID, mainKey);
  const legacyMainAliasKey = buildMainSessionKey(FALLBACK_DEFAULT_AGENT_ID, "main");
  const isMainAlias = raw === "main" || raw === mainKey || raw === agentMainSessionKey || raw === agentMainAliasKey || raw === legacyMainKey || raw === legacyMainAliasKey;
  if (params.cfg?.session?.scope === "global" && isMainAlias) return "global";
  if (isMainAlias) return agentMainSessionKey;
  return raw;
}
//#endregion /* v9-0d348c9fda166464 */
