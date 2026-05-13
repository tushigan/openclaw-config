"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromUnion = FromUnion;
var _index = require("../../guard/index.mjs");
var _callback = require("./callback.mjs");
var _from_type = require("./from_type.mjs");
var _index2 = require("../clone/index.mjs");
var _index3 = require("../check/index.mjs");
var _union_priority_sort = require("../shared/union_priority_sort.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Decode
// ------------------------------------------------------------------
function Decode(direction, context, type, value) {
  for (const schema of (0, _union_priority_sort.UnionPrioritySort)(type.anyOf, 1)) {
    if (!(0, _index3.Check)(context, schema, value))
    continue;
    const variant = (0, _from_type.FromType)(direction, context, schema, value);
    return (0, _callback.Callback)(direction, context, type, variant);
  }
  return value;
}
// ------------------------------------------------------------------
// Encode
// ------------------------------------------------------------------
function Encode(direction, context, type, value) {
  const exterior = (0, _callback.Callback)(direction, context, type, value);
  for (const schema of (0, _union_priority_sort.UnionPrioritySort)(type.anyOf, -1)) {
    const variant = (0, _from_type.FromType)(direction, context, schema, (0, _index2.Clone)(exterior));
    if (!(0, _index3.Check)(context, schema, variant))
    continue;
    return variant;
  }
  return exterior;
}
// ------------------------------------------------------------------
// FromUnion
// ------------------------------------------------------------------
function FromUnion(direction, context, type, value) {
  return _index.Guard.IsEqual(direction, 'Decode') ?
  Decode(direction, context, type, value) :
  Encode(direction, context, type, value);
} /* v9-ba23c7c4e7792a8c */
