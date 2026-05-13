"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromTuple = FromTuple;
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
  for (let i = 0; i < Math.min(type.items.length, value.length); i++) {
    value[i] = (0, _from_type.FromType)(direction, context, type.items[i], value[i]);
  }
  return (0, _callback.Callback)(direction, context, type, value);
}
// ------------------------------------------------------------------
// Encode
// ------------------------------------------------------------------
function Encode(direction, context, type, value) {
  const exterior = (0, _callback.Callback)(direction, context, type, value);
  if (!_index2.Guard.IsArray(exterior))
  return value;
  for (let i = 0; i < Math.min(type.items.length, exterior.length); i++) {
    exterior[i] = (0, _from_type.FromType)(direction, context, type.items[i], exterior[i]);
  }
  return exterior;
}
function FromTuple(direction, context, type, value) {
  return _index2.Guard.IsEqual(direction, 'Decode') ?
  Decode(direction, context, type, value) :
  Encode(direction, context, type, value);
} /* v9-5862f18e2af35c2e */
