"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromArray = FromArray;
var _index = require("../../system/unreachable/index.mjs");
var _index2 = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs");
var _callback = require("./callback.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Decode
// ------------------------------------------------------------------
function Decode(direction, context, type, value) {
  // deno-coverage-ignore-start - unreachable | checked
  if (!_index2.Guard.IsArray(value))
  return (0, _index.Unreachable)();
  // deno-coverage-ignore-stop
  for (let i = 0; i < value.length; i++) {
    value[i] = (0, _from_type.FromType)(direction, context, type.items, value[i]);
  }
  return (0, _callback.Callback)(direction, context, type, value);
}
// ------------------------------------------------------------------
// Encode
// ------------------------------------------------------------------
function Encode(direction, context, type, value) {
  const exterior = (0, _callback.Callback)(direction, context, type, value);
  if (!_index2.Guard.IsArray(exterior))
  return exterior;
  for (let i = 0; i < exterior.length; i++) {
    exterior[i] = (0, _from_type.FromType)(direction, context, type.items, exterior[i]);
  }
  return exterior;
}
// ------------------------------------------------------------------
// FromArray
// ------------------------------------------------------------------
function FromArray(direction, context, type, value) {
  return _index2.Guard.IsEqual(direction, 'Decode') ?
  Decode(direction, context, type, value) :
  Encode(direction, context, type, value);
} /* v9-aa48622aa8d10d55 */
