"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromIntersect = FromIntersect;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs");
var _callback = require("./callback.mjs");
var _index2 = require("../clone/index.mjs");
var _index3 = require("../clean/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// MergeInteriors
//
// Merges all interior operand results into a single object. Each
// subsequent operand's properties override those of prior operands.
//
// ------------------------------------------------------------------
function MergeInteriors(interiors) {
  return interiors.reduce((results, interior) => ({ ...results, ...interior }), {});
}
// ------------------------------------------------------------------
// NonMatchingInterior
//
// Used when Intersect operands do not all produce Objects. Returns
// the first interior result that differs from the original value,
// indicating a Codec has transformed the data. If no operand
// produced a change, defaults to the first interior result.
//
// ------------------------------------------------------------------
function NonMatchingInterior(value, interiors) {
  for (const interior of interiors)
  if (!_index.Guard.IsDeepEqual(value, interior))
  return interior;
  return value; // value-unchanged
}
// ------------------------------------------------------------------
// Decode
// ------------------------------------------------------------------
function Decode(direction, context, type, value) {
  if (_index.Guard.IsEqual(type.allOf.length, 0))
  return (0, _callback.Callback)(direction, context, type, value);
  const interiors = type.allOf.map((schema) => (0, _from_type.FromType)(direction, context, schema, (0, _index3.Clean)(schema, (0, _index2.Clone)(value))));
  const structural = interiors.every((result) => _index.Guard.IsObject(result));
  const exterior = structural ? MergeInteriors(interiors) : NonMatchingInterior(value, interiors);
  return (0, _callback.Callback)(direction, context, type, exterior);
}
// ------------------------------------------------------------------
// Encode
// ------------------------------------------------------------------
function Encode(direction, context, type, value) {
  if (_index.Guard.IsEqual(type.allOf.length, 0))
  return (0, _callback.Callback)(direction, context, type, value);
  const exterior = (0, _callback.Callback)(direction, context, type, value);
  const interiors = type.allOf.map((schema) => (0, _from_type.FromType)(direction, context, schema, (0, _index3.Clean)(schema, (0, _index2.Clone)(exterior))));
  const structural = interiors.every((result) => _index.Guard.IsObject(result));
  if (structural)
  return MergeInteriors(interiors);
  return NonMatchingInterior(exterior, interiors);
}
function FromIntersect(direction, context, type, value) {
  return _index.Guard.IsEqual(direction, 'Decode') ? Decode(direction, context, type, value) : Encode(direction, context, type, value);
} /* v9-054e5aa029ba50bc */
