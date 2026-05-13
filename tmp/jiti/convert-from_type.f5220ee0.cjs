"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromType = FromType;
var Type = _interopRequireWildcard(require("../../type/index.mjs"));
var _from_array = require("./from_array.mjs");
var _from_base = require("./from_base.mjs");
var _from_bigint = require("./from_bigint.mjs");
var _from_boolean = require("./from_boolean.mjs");
var _from_cyclic = require("./from_cyclic.mjs");
var _from_enum = require("./from_enum.mjs");
var _from_integer = require("./from_integer.mjs");
var _from_intersect = require("./from_intersect.mjs");
var _from_literal = require("./from_literal.mjs");
var _from_null = require("./from_null.mjs");
var _from_number = require("./from_number.mjs");
var _from_object = require("./from_object.mjs");
var _from_record = require("./from_record.mjs");
var _from_ref = require("./from_ref.mjs");
var _from_string = require("./from_string.mjs");
var _from_template_literal = require("./from_template_literal.mjs");
var _from_tuple = require("./from_tuple.mjs");
var _from_undefined = require("./from_undefined.mjs");
var _from_union = require("./from_union.mjs");
var _from_void = require("./from_void.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
function FromType(context, type, value) {
  return Type.IsArray(type) ? (0, _from_array.FromArray)(context, type, value) :
  Type.IsBase(type) ? (0, _from_base.FromBase)(context, type, value) :
  Type.IsBigInt(type) ? (0, _from_bigint.FromBigInt)(context, type, value) :
  Type.IsBoolean(type) ? (0, _from_boolean.FromBoolean)(context, type, value) :
  Type.IsCyclic(type) ? (0, _from_cyclic.FromCyclic)(context, type, value) :
  Type.IsEnum(type) ? (0, _from_enum.FromEnum)(context, type, value) :
  Type.IsInteger(type) ? (0, _from_integer.FromInteger)(context, type, value) :
  Type.IsIntersect(type) ? (0, _from_intersect.FromIntersect)(context, type, value) :
  Type.IsLiteral(type) ? (0, _from_literal.FromLiteral)(context, type, value) :
  Type.IsNull(type) ? (0, _from_null.FromNull)(context, type, value) :
  Type.IsNumber(type) ? (0, _from_number.FromNumber)(context, type, value) :
  Type.IsObject(type) ? (0, _from_object.FromObject)(context, type, value) :
  Type.IsRecord(type) ? (0, _from_record.FromRecord)(context, type, value) :
  Type.IsRef(type) ? (0, _from_ref.FromRef)(context, type, value) :
  Type.IsString(type) ? (0, _from_string.FromString)(context, type, value) :
  Type.IsTemplateLiteral(type) ? (0, _from_template_literal.FromTemplateLiteral)(context, type, value) :
  Type.IsTuple(type) ? (0, _from_tuple.FromTuple)(context, type, value) :
  Type.IsUndefined(type) ? (0, _from_undefined.FromUndefined)(context, type, value) :
  Type.IsUnion(type) ? (0, _from_union.FromUnion)(context, type, value) :
  Type.IsVoid(type) ? (0, _from_void.FromVoid)(context, type, value) :
  value;
} /* v9-435d6653d4da1ca0 */
