"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromObject = FromObject;
var _index = require("../../system/unreachable/index.mjs");
var _index2 = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs");
var _callback = require("./callback.mjs");
var _optional_undefined = require("../shared/optional_undefined.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Decode
// ------------------------------------------------------------------
function Decode(direction, context, type, value) {
  // deno-coverage-ignore-start - unreachable | checked
  if (!_index2.Guard.IsObjectNotArray(value))
  return (0, _index.Unreachable)();
  // deno-coverage-ignore-stop
  for (const key of _index2.Guard.Keys(type.properties)) {
    // Ignore for non-present or optional-undefined
    if (!_index2.Guard.HasPropertyKey(value, key) || (0, _optional_undefined.IsOptionalUndefined)(type.properties[key], key, value))
    continue;
    value[key] = (0, _from_type.FromType)(direction, context, type.properties[key], value[key]);
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
  for (const key of _index2.Guard.Keys(type.properties)) {
    // Ignore for non-present or optional-undefined
    if (!_index2.Guard.HasPropertyKey(exterior, key) || (0, _optional_undefined.IsOptionalUndefined)(type.properties[key], key, exterior))
    continue;
    exterior[key] = (0, _from_type.FromType)(direction, context, type.properties[key], exterior[key]);
  }
  return exterior;
}
// ------------------------------------------------------------------
// FromObject
// ------------------------------------------------------------------
function FromObject(direction, context, type, value) {
  return _index2.Guard.IsEqual(direction, 'Decode') ?
  Decode(direction, context, type, value) :
  Encode(direction, context, type, value);
} /* v9-c443f7131d0fffc7 */
