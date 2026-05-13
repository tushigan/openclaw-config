"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = resolveAgentRuntimePolicy; //#region src/agents/agent-runtime-policy.ts
function resolveAgentRuntimePolicy(container) {
  const preferred = container?.agentRuntime;
  if (hasAgentRuntimePolicy(preferred)) return preferred;
}
function hasAgentRuntimePolicy(value) {
  return Boolean(value?.id?.trim());
}
//#endregion /* v9-f7ebf6019c3a773c */
