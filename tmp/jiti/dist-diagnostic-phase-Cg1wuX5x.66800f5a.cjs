"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.i = withDiagnosticPhase;exports.n = getRecentDiagnosticPhases;exports.r = resetDiagnosticPhasesForTest;exports.t = getCurrentDiagnosticPhase;var _diagnosticEventsCjwOnQj = require("./diagnostic-events-CjwOn-Qj.js");
var _nodePerf_hooks = require("node:perf_hooks");
//#region src/logging/diagnostic-phase.ts
const RECENT_PHASE_CAPACITY = 40;
let activePhaseStack = [];
let recentPhases = [];
function roundMetric(value, digits = 1) {
  if (!Number.isFinite(value)) return 0;
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}
function pushRecentPhase(snapshot) {
  recentPhases.push(snapshot);
  if (recentPhases.length > RECENT_PHASE_CAPACITY) recentPhases = recentPhases.slice(-RECENT_PHASE_CAPACITY);
}
function getCurrentDiagnosticPhase() {
  return activePhaseStack.at(-1)?.name;
}
function getRecentDiagnosticPhases(limit = 8) {
  return recentPhases.slice(-Math.max(0, limit)).map((phase) => Object.assign({}, phase));
}
function recordDiagnosticPhase(snapshot) {
  pushRecentPhase(snapshot);
  if (!(0, _diagnosticEventsCjwOnQj.t)()) return;
  (0, _diagnosticEventsCjwOnQj.n)({
    type: "diagnostic.phase.completed",
    ...snapshot
  });
}
async function withDiagnosticPhase(name, run, details) {
  const active = {
    name,
    startedAt: Date.now(),
    startedWallMs: _nodePerf_hooks.performance.now(),
    cpuStarted: process.cpuUsage(),
    details
  };
  activePhaseStack.push(active);
  try {
    return await run();
  } finally {
    const endedAt = Date.now();
    const durationMs = roundMetric(_nodePerf_hooks.performance.now() - active.startedWallMs, 1);
    const cpu = process.cpuUsage(active.cpuStarted);
    const cpuUserMs = roundMetric(cpu.user / 1e3, 1);
    const cpuSystemMs = roundMetric(cpu.system / 1e3, 1);
    const cpuTotalMs = roundMetric(cpuUserMs + cpuSystemMs, 1);
    activePhaseStack = activePhaseStack.filter((entry) => entry !== active);
    recordDiagnosticPhase({
      name,
      startedAt: active.startedAt,
      endedAt,
      durationMs,
      cpuUserMs,
      cpuSystemMs,
      cpuTotalMs,
      cpuCoreRatio: roundMetric(cpuTotalMs / Math.max(1, durationMs), 3),
      details: active.details
    });
  }
}
function resetDiagnosticPhasesForTest() {
  activePhaseStack = [];
  recentPhases = [];
}
//#endregion /* v9-24701f17c0565199 */
