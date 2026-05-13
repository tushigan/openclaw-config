"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = resolveProcessScopedMap; //#region src/shared/process-scoped-map.ts
function resolveProcessScopedMap(key) {
  const proc = process;
  const existing = proc[key];
  if (existing) return existing;
  const created = /* @__PURE__ */new Map();
  proc[key] = created;
  return created;
}
//#endregion /* v9-7d5dfa4ff344cf51 */
