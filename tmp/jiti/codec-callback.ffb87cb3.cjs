"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Callback = Callback;
var _index = require("../../guard/index.mjs");
var _index2 = require("../../type/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Decode
// ------------------------------------------------------------------
function Decode(_context, type, value) {
  return type['~codec'].decode(value);
}
// ------------------------------------------------------------------
// Encode
// ------------------------------------------------------------------
function Encode(_context, type, value) {
  return type['~codec'].encode(value);
}
// ------------------------------------------------------------------
// Callback
// ------------------------------------------------------------------
function Callback(direction, context, type, value) {
  if (!(0, _index2.IsCodec)(type))
  return value;
  return _index.Guard.IsEqual(direction, 'Decode') ?
  Decode(context, type, value) :
  Encode(context, type, value);
} /* v9-af2ae5c51f48afa0 */
