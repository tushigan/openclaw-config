"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.a = shouldLogVerbose;exports.i = logVerboseConsole;exports.o = exports.n = void 0;exports.r = logVerbose;exports.t = exports.s = void 0;var _themeCVJvORNs = require("./theme-CVJvORNs.js");
var _loggerBVNXvwCE = require("./logger-BVNXvwCE.js");
//#region src/globals.ts
function shouldLogVerbose() {
  return (0, _loggerBVNXvwCE.b)() || (0, _loggerBVNXvwCE.s)("debug");
}
function logVerbose(message) {
  if (!shouldLogVerbose()) return;
  try {
    (0, _loggerBVNXvwCE.a)().debug({ message }, "verbose");
  } catch {}
  if (!(0, _loggerBVNXvwCE.b)()) return;
  console.log(_themeCVJvORNs.r.muted(message));
}
function logVerboseConsole(message) {
  if (!(0, _loggerBVNXvwCE.b)()) return;
  console.log(_themeCVJvORNs.r.muted(message));
}
const success = exports.o = _themeCVJvORNs.r.success;
const warn = exports.s = _themeCVJvORNs.r.warn;
const info = exports.n = _themeCVJvORNs.r.info;
const danger = exports.t = _themeCVJvORNs.r.error;
//#endregion /* v9-5c2fb71e83dea4e0 */
