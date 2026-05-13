"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Fail = Fail;exports.IsOk = IsOk;exports.Ok = Ok;
var _index = require("../../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
function IsOk(value) {
  return _index.Guard.IsObject(value) && _index.Guard.HasPropertyKey(value, 'value');
}
// ------------------------------------------------------------------
// Factory
// ------------------------------------------------------------------
function Ok(value) {
  return { value };
}
function Fail() {
  return undefined;
} /* v9-6426bab7d3b57374 */
