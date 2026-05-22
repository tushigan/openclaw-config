"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.t = summarizeStringEntries; //#region src/shared/string-sample.ts
function summarizeStringEntries(params) {
  const entries = params.entries ?? [];
  if (entries.length === 0) return params.emptyText ?? "";
  const limit = Math.max(1, Math.floor(params.limit ?? 6));
  const sample = entries.slice(0, limit);
  const suffix = entries.length > sample.length ? ` (+${entries.length - sample.length})` : "";
  return `${sample.join(", ")}${suffix}`;
}
//#endregion /* v9-e0b840094e36a010 */
