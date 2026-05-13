"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromRecord = FromRecord;
var _index = require("../../system/unreachable/index.mjs");
var _index2 = require("../../guard/index.mjs");
var _index3 = require("../../type/index.mjs");
var _from_type = require("./from_type.mjs");
var _callback = require("./callback.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Decode
// ------------------------------------------------------------------
function Decode(direction, context, type, value) {
  // deno-coverage-ignore-start - unreachable | checked
  if (!_index2.Guard.IsObjectNotArray(value))
  return (0, _index.Unreachable)();
  // deno-coverage-ignore-stop
  const regexp = new RegExp((0, _index3.RecordPattern)(type));
  for (const key of _index2.Guard.Keys(value)) {
    // deno-coverage-ignore-start - unreachable | checked
    if (!regexp.test(key))
    (0, _index.Unreachable)();
    // deno-coverage-ignore-stop
    value[key] = (0, _from_type.FromType)(direction, context, (0, _index3.RecordValue)(type), value[key]);
  }
  return (0, _callback.Callback)(direction, context, type, value);
}
// ------------------------------------------------------------------
// Encode
// ------------------------------------------------------------------
function Encode(direction, context, type, value) {
  const exterior = (0, _callback.Callback)(direction, context, type, value);
  if (!_index2.Guard.IsObjectNotArray(exterior))
  return exterior;
  const regexp = new RegExp((0, _index3.RecordPattern)(type));
  for (const key of _index2.Guard.Keys(exterior)) {
    if (!regexp.test(key))
    continue;
    exterior[key] = (0, _from_type.FromType)(direction, context, (0, _index3.RecordValue)(type), exterior[key]);
  }
  return exterior;
}
function FromRecord(direction, context, type, value) {
  return _index2.Guard.IsEqual(direction, 'Decode') ?
  Decode(direction, context, type, value) :
  Encode(direction, context, type, value);
} /* v9-fae0f665b2046771 */
