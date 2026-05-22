"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = resolveThreadBindingThreadName;exports.n = resolveThreadBindingFarewellText;exports.r = resolveThreadBindingIntroText;exports.t = formatThreadBindingDurationLabel;var _stringCoerceBje8XVt = require("./string-coerce-Bje8XVt9.js");
var _systemMessageCgjcToJM = require("./system-message-CgjcToJM.js");
//#region src/channels/thread-bindings-messages.ts
const DEFAULT_THREAD_BINDING_FAREWELL_TEXT = "Session ended. Messages here will no longer be routed.";
function normalizeThreadBindingDurationMs(raw) {
  if (typeof raw !== "number" || !Number.isFinite(raw)) return 0;
  const durationMs = Math.floor(raw);
  if (durationMs < 0) return 0;
  return durationMs;
}
function formatThreadBindingDurationLabel(durationMs) {
  if (durationMs <= 0) return "disabled";
  if (durationMs < 6e4) return "<1m";
  const totalMinutes = Math.floor(durationMs / 6e4);
  if (totalMinutes % 60 === 0) return `${Math.floor(totalMinutes / 60)}h`;
  return `${totalMinutes}m`;
}
function resolveThreadBindingThreadName(params) {
  return `🤖 ${(0, _stringCoerceBje8XVt.c)(params.label) || (0, _stringCoerceBje8XVt.c)(params.agentId) || "agent"}`.replace(/\s+/g, " ").trim().slice(0, 100);
}
function resolveThreadBindingIntroText(params) {
  const normalized = ((0, _stringCoerceBje8XVt.c)(params.label) || (0, _stringCoerceBje8XVt.c)(params.agentId) || "agent").replace(/\s+/g, " ").trim().slice(0, 100) || "agent";
  const idleTimeoutMs = normalizeThreadBindingDurationMs(params.idleTimeoutMs);
  const maxAgeMs = normalizeThreadBindingDurationMs(params.maxAgeMs);
  const cwd = (0, _stringCoerceBje8XVt.c)(params.sessionCwd);
  const details = (params.sessionDetails ?? []).map((entry) => entry.trim()).filter((entry) => entry.length > 0);
  if (cwd) details.unshift(`cwd: ${cwd}`);
  const lifecycle = [];
  if (idleTimeoutMs > 0) lifecycle.push(`idle auto-unfocus after ${formatThreadBindingDurationLabel(idleTimeoutMs)} inactivity`);
  if (maxAgeMs > 0) lifecycle.push(`max age ${formatThreadBindingDurationLabel(maxAgeMs)}`);
  const intro = lifecycle.length > 0 ? `${normalized} session active (${lifecycle.join("; ")}). Messages here go directly to this session.` : `${normalized} session active. Messages here go directly to this session.`;
  if (details.length === 0) return (0, _systemMessageCgjcToJM.r)(intro);
  return (0, _systemMessageCgjcToJM.r)(`${intro}\n${details.join("\n")}`);
}
function resolveThreadBindingFarewellText(params) {
  const custom = (0, _stringCoerceBje8XVt.c)(params.farewellText);
  if (custom) return (0, _systemMessageCgjcToJM.r)(custom);
  if (params.reason === "idle-expired") return (0, _systemMessageCgjcToJM.r)(`Session ended automatically after ${formatThreadBindingDurationLabel(normalizeThreadBindingDurationMs(params.idleTimeoutMs))} of inactivity. Messages here will no longer be routed.`);
  if (params.reason === "max-age-expired") return (0, _systemMessageCgjcToJM.r)(`Session ended automatically at max age of ${formatThreadBindingDurationLabel(normalizeThreadBindingDurationMs(params.maxAgeMs))}. Messages here will no longer be routed.`);
  return (0, _systemMessageCgjcToJM.r)(DEFAULT_THREAD_BINDING_FAREWELL_TEXT);
}
//#endregion /* v9-25d764e9da1f4ab0 */
