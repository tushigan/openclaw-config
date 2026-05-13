"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromRef = FromRef;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs");
var _callback = require("./callback.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// ResolveRef
// ------------------------------------------------------------------
function ResolveRef(direction, context, type, value) {
  return _index.Guard.HasPropertyKey(context, type.$ref) ?
  (0, _from_type.FromType)(direction, context, context[type.$ref], value) :
  value;
}
// ------------------------------------------------------------------
// FromRef
//
// Decode and Encode apply the Callback and the referenced type's
// codec pipeline in opposite orders, since the two operations are
// inverses of each other.
//
// Decode: referenced type resolves first, Callback runs after.
//   wire value -> resolve $ref -> Callback -> decoded value
//
// Encode: Callback runs first, referenced type resolves after.
//   encoded value -> Callback -> resolve $ref -> wire value
//
// ------------------------------------------------------------------
function FromRef(direction, context, type, value) {
  return _index.Guard.IsEqual(direction, 'Decode') ?
  (0, _callback.Callback)(direction, context, type, ResolveRef(direction, context, type, value)) :
  ResolveRef(direction, context, type, (0, _callback.Callback)(direction, context, type, value));
} /* v9-8aad6398b57fe32b */
