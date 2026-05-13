"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = markDiagnosticActivity;exports.i = logLaneEnqueue;exports.n = getLastDiagnosticActivityAt;exports.o = resetDiagnosticActivityForTest;exports.r = logLaneDequeue;exports.t = void 0;var _diagnosticEventsCjwOnQj = require("./diagnostic-events-CjwOn-Qj.js");
var _subsystemCxWoQXRD = require("./subsystem-CxWoQXRD.js");
//#region src/logging/diagnostic-runtime.ts
const diag = (0, _subsystemCxWoQXRD.t)("diagnostic");
let lastActivityAt = 0;
const diagnosticLogger = exports.t = diag;
function markDiagnosticActivity() {
  lastActivityAt = Date.now();
}
function getLastDiagnosticActivityAt() {
  return lastActivityAt;
}
function resetDiagnosticActivityForTest() {
  lastActivityAt = 0;
}
function logLaneEnqueue(lane, queueSize) {
  if (!(0, _diagnosticEventsCjwOnQj.t)()) return;
  diag.debug(`lane enqueue: lane=${lane} queueSize=${queueSize}`);
  (0, _diagnosticEventsCjwOnQj.n)({
    type: "queue.lane.enqueue",
    lane,
    queueSize
  });
  markDiagnosticActivity();
}
function logLaneDequeue(lane, waitMs, queueSize) {
  if (!(0, _diagnosticEventsCjwOnQj.t)()) return;
  diag.debug(`lane dequeue: lane=${lane} waitMs=${waitMs} queueSize=${queueSize}`);
  (0, _diagnosticEventsCjwOnQj.n)({
    type: "queue.lane.dequeue",
    lane,
    queueSize,
    waitMs
  });
  markDiagnosticActivity();
}
//#endregion /* v9-a2688895bc3bc10f */
