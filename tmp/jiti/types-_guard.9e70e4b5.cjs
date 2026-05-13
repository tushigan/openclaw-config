"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsGuard = IsGuard;exports.IsGuardInterface = IsGuardInterface;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
function IsGuardInterface(value) {
  return _index.Guard.IsObject(value) &&
  _index.Guard.HasPropertyKey(value, 'check') &&
  _index.Guard.HasPropertyKey(value, 'errors') &&
  _index.Guard.IsFunction(value.check) &&
  _index.Guard.IsFunction(value.errors);
}
function IsGuard(value) {
  return _index.Guard.HasPropertyKey(value, '~guard') &&
  IsGuardInterface(value['~guard']);
} /* v9-3d405457e625df86 */
