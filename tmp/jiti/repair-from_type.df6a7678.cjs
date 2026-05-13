"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromType = FromType;
var _index = require("../../guard/index.mjs");
var T = _interopRequireWildcard(require("../../type/index.mjs"));
var _index3 = require("../check/index.mjs");
var _index4 = require("../create/index.mjs");
var _from_array = require("./from_array.mjs");
var _from_base = require("./from_base.mjs");
var _from_enum = require("./from_enum.mjs");
var _from_intersect = require("./from_intersect.mjs");
var _from_object = require("./from_object.mjs");
var _from_record = require("./from_record.mjs");
var _from_ref = require("./from_ref.mjs");
var _from_template_literal = require("./from_template_literal.mjs");
var _from_tuple = require("./from_tuple.mjs");
var _from_union = require("./from_union.mjs");
var _from_unknown = require("./from_unknown.mjs");
var _error = require("./error.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// AssertRepairableValue
// ------------------------------------------------------------------
function AssertRepairableValue(context, type, value) {
  const unsupported = _index.GlobalsGuard.IsDate(value) ||
  _index.GlobalsGuard.IsMap(value) ||
  _index.GlobalsGuard.IsSet(value) ||
  _index.GlobalsGuard.IsTypeArray(value) ||
  _index.Guard.IsConstructor(value) ||
  _index.Guard.IsFunction(value);
  if (unsupported) {
    throw new _error.RepairError(context, type, value, 'Value is not repairable');
  }
}
// ------------------------------------------------------------------
// AssertRepairableType
// ------------------------------------------------------------------
function AssertRepairableType(context, type, value) {
  const unsupported = T.IsAsyncIterator(type) ||
  T.IsIterator(type) ||
  T.IsConstructor(type) ||
  T.IsFunction(type) ||
  T.IsNever(type) ||
  T.IsPromise(type);
  if (unsupported) {
    throw new _error.RepairError(context, type, value, 'Type is not repairable');
  }
}
// ------------------------------------------------------------------
// FinalizeRepair
//
// When a type includes the ~refine modifier, a post-repair validation
// check must be performed to ensure the repaired value satisfies the
// refine constraint. This logic is implemented as part of FromType to
// ensure the post-refine validation check is handled outside of
// sub-schema constraint checking (i.e., at the top level).
//
// ------------------------------------------------------------------
function FinalizeRepair(context, type, repaired) {
  return T.IsRefine(type) ?
  (0, _index3.Check)(context, type, repaired) ?
  repaired :
  (0, _index4.Create)(context, type) :
  repaired;
}
// ------------------------------------------------------------------
// FromType
// ------------------------------------------------------------------
function FromType(context, type, value) {
  // Base Repair
  if (T.IsBase(type)) {
    const repaired = (0, _from_base.FromBase)(context, type, value);
    return FinalizeRepair(context, type, repaired);
  }
  // Schema Repair
  AssertRepairableValue(context, type, value);
  AssertRepairableType(context, type, value);
  const repaired = T.IsArray(type) ? (0, _from_array.FromArray)(context, type, value) :
  T.IsEnum(type) ? (0, _from_enum.FromEnum)(context, type, value) :
  T.IsIntersect(type) ? (0, _from_intersect.FromIntersect)(context, type, value) :
  T.IsObject(type) ? (0, _from_object.FromObject)(context, type, value) :
  T.IsRecord(type) ? (0, _from_record.FromRecord)(context, type, value) :
  T.IsRef(type) ? (0, _from_ref.FromRef)(context, type, value) :
  T.IsTemplateLiteral(type) ? (0, _from_template_literal.FromTemplateLiteral)(context, type, value) :
  T.IsTuple(type) ? (0, _from_tuple.FromTuple)(context, type, value) :
  T.IsUnion(type) ? (0, _from_union.FromUnion)(context, type, value) :
  (0, _from_unknown.FromUnknown)(context, type, value);
  return FinalizeRepair(context, type, repaired);
} /* v9-0b83f3d0cbd5fa02 */
