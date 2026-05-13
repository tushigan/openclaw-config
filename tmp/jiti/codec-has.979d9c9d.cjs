"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.HasCodec = HasCodec;
var _index = require("../../system/arguments/index.mjs");
var _index2 = require("../../guard/index.mjs");
var _index3 = require("../../type/index.mjs"); // deno-fmt-ignore-file








// ------------------------------------------------------------------
// Array
// ------------------------------------------------------------------
function FromArray(context, type) {
  return (0, _index3.IsCodec)(type) || FromType(context, type.items);
}
// ------------------------------------------------------------------
// Cyclic
// ------------------------------------------------------------------
function FromCyclic(context, type) {
  return (0, _index3.IsCodec)(type) || FromRef({ ...context, ...type.$defs }, (0, _index3.Ref)(type.$ref));
}
// ------------------------------------------------------------------
// Intersect
// ------------------------------------------------------------------
function FromIntersect(context, type) {
  return (0, _index3.IsCodec)(type) || type.allOf.some((type) => FromType(context, type));
}
// ------------------------------------------------------------------
// Object
// ------------------------------------------------------------------
function FromObject(context, type) {
  return (0, _index3.IsCodec)(type) || _index2.Guard.Keys(type.properties).some((key) => {
    return FromType(context, type.properties[key]);
  });
}
// ------------------------------------------------------------------
// Record
// ------------------------------------------------------------------
function FromRecord(context, type) {
  return (0, _index3.IsCodec)(type) || FromType(context, (0, _index3.RecordValue)(type));
}
// ------------------------------------------------------------------
// Ref
// ------------------------------------------------------------------
function FromRef(context, type) {
  if (visited.has(type.$ref))
  return false;
  visited.add(type.$ref);
  return (0, _index3.IsCodec)(type) || _index2.Guard.HasPropertyKey(context, type.$ref) &&
  FromType(context, context[type.$ref]);
}
// ------------------------------------------------------------------
// Tuple
// ------------------------------------------------------------------
function FromTuple(context, type) {
  return (0, _index3.IsCodec)(type) || type.items.some((type) => FromType(context, type));
}
// ------------------------------------------------------------------
// Union
// ------------------------------------------------------------------
function FromUnion(context, type) {
  return (0, _index3.IsCodec)(type) || type.anyOf.some((type) => FromType(context, type));
}
// ------------------------------------------------------------------
// Type
// ------------------------------------------------------------------
function FromType(context, type) {
  return (0, _index3.IsArray)(type) ? FromArray(context, type) :
  (0, _index3.IsCyclic)(type) ? FromCyclic(context, type) :
  (0, _index3.IsIntersect)(type) ? FromIntersect(context, type) :
  (0, _index3.IsObject)(type) ? FromObject(context, type) :
  (0, _index3.IsRecord)(type) ? FromRecord(context, type) :
  (0, _index3.IsRef)(type) ? FromRef(context, type) :
  (0, _index3.IsTuple)(type) ? FromTuple(context, type) :
  (0, _index3.IsUnion)(type) ? FromUnion(context, type) :
  (0, _index3.IsCodec)(type);
}
// ------------------------------------------------------------------
// Visited
// ------------------------------------------------------------------
const visited = new Set();
/** Returns true if this type contains a Codec */
function HasCodec(...args) {
  const [context, type] = _index.Arguments.Match(args, {
    2: (context, type) => [context, type],
    1: (type) => [{}, type]
  });
  visited.clear();
  return FromType(context, type);
} /* v9-c6c2ca0974ddbfe4 */
