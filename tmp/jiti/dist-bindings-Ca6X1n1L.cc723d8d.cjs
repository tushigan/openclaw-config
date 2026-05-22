"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = resolvePreferredAccountId;exports.i = resolveDefaultAgentBoundAccountId;exports.n = listBindings;exports.r = listBoundAccountIds;exports.t = buildChannelAccountBindings;var _sessionKeyC0K0uhmG = require("./session-key-C0K0uhmG.js");
var _agentScopeB6RIBoEj = require("./agent-scope-B6RIBoEj.js");
var _bindingsDF2SAWWF = require("./bindings-DF2SAWWF.js");
var _bindingScope24gbnUFq = require("./binding-scope-24gbnUFq.js");
//#region src/routing/bindings.ts
function listBindings(cfg) {
  return (0, _bindingsDF2SAWWF.i)(cfg);
}
function listBoundAccountIds(cfg, channelId) {
  const normalizedChannel = (0, _bindingScope24gbnUFq.t)(channelId);
  if (!normalizedChannel) return [];
  const ids = /* @__PURE__ */new Set();
  for (const binding of listBindings(cfg)) {
    const resolved = (0, _bindingScope24gbnUFq.i)(binding);
    if (!resolved || resolved.channelId !== normalizedChannel) continue;
    ids.add(resolved.accountId);
  }
  return Array.from(ids).toSorted((a, b) => a.localeCompare(b));
}
function resolveDefaultAgentBoundAccountId(cfg, channelId) {
  const normalizedChannel = (0, _bindingScope24gbnUFq.t)(channelId);
  if (!normalizedChannel) return null;
  const defaultAgentId = (0, _sessionKeyC0K0uhmG.c)((0, _agentScopeB6RIBoEj.S)(cfg));
  for (const binding of listBindings(cfg)) {
    const resolved = (0, _bindingScope24gbnUFq.i)(binding);
    if (!resolved || resolved.channelId !== normalizedChannel || resolved.agentId !== defaultAgentId) continue;
    return resolved.accountId;
  }
  return null;
}
function buildChannelAccountBindings(cfg) {
  const map = /* @__PURE__ */new Map();
  for (const binding of listBindings(cfg)) {
    const resolved = (0, _bindingScope24gbnUFq.i)(binding);
    if (!resolved) continue;
    const byAgent = map.get(resolved.channelId) ?? /* @__PURE__ */new Map();
    const list = byAgent.get(resolved.agentId) ?? [];
    if (!list.includes(resolved.accountId)) list.push(resolved.accountId);
    byAgent.set(resolved.agentId, list);
    map.set(resolved.channelId, byAgent);
  }
  return map;
}
function resolvePreferredAccountId(params) {
  if (params.boundAccounts.length > 0) return params.boundAccounts[0];
  return params.defaultAccountId;
}
//#endregion /* v9-603ee69374f5f3da */
