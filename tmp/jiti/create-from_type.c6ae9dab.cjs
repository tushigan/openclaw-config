"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromType = FromType;
var T = _interopRequireWildcard(require("../../type/index.mjs"));
var S = _interopRequireWildcard(require("../../schema/types/index.mjs"));
var _from_default = require("./from_default.mjs");
var _from_array = require("./from_array.mjs");
var _from_async_iterator = require("./from_async_iterator.mjs");
var _from_base = require("./from_base.mjs");
var _from_bigint = require("./from_bigint.mjs");
var _from_boolean = require("./from_boolean.mjs");
var _from_constructor = require("./from_constructor.mjs");
var _from_cyclic = require("./from_cyclic.mjs");
var _from_enum = require("./from_enum.mjs");
var _from_function = require("./from_function.mjs");
var _from_integer = require("./from_integer.mjs");
var _from_intersect = require("./from_intersect.mjs");
var _from_iterator = require("./from_iterator.mjs");
var _from_literal = require("./from_literal.mjs");
var _from_never = require("./from_never.mjs");
var _from_null = require("./from_null.mjs");
var _from_number = require("./from_number.mjs");
var _from_object = require("./from_object.mjs");
var _from_promise = require("./from_promise.mjs");
var _from_record = require("./from_record.mjs");
var _from_ref = require("./from_ref.mjs");
var _from_string = require("./from_string.mjs");
var _from_symbol = require("./from_symbol.mjs");
var _from_template_literal = require("./from_template_literal.mjs");
var _from_tuple = require("./from_tuple.mjs");
var _from_undefined = require("./from_undefined.mjs");
var _from_union = require("./from_union.mjs");
var _from_void = require("./from_void.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
function FromType(context, type) {
  return (
    // -----------------------------------------------------
    // Default
    // -----------------------------------------------------
    S.IsDefault(type) ? (0, _from_default.FromDefault)(context, type) :
    // -----------------------------------------------------
    // Types
    // -----------------------------------------------------
    T.IsArray(type) ? (0, _from_array.FromArray)(context, type) :
    T.IsAsyncIterator(type) ? (0, _from_async_iterator.FromAsyncIterator)(context, type) :
    T.IsBase(type) ? (0, _from_base.FromBase)(context, type) :
    T.IsBigInt(type) ? (0, _from_bigint.FromBigInt)(context, type) :
    T.IsBoolean(type) ? (0, _from_boolean.FromBoolean)(context, type) :
    T.IsConstructor(type) ? (0, _from_constructor.FromConstructor)(context, type) :
    T.IsCyclic(type) ? (0, _from_cyclic.FromCyclic)(context, type) :
    T.IsEnum(type) ? (0, _from_enum.FromEnum)(context, type) :
    T.IsFunction(type) ? (0, _from_function.FromFunction)(context, type) :
    T.IsInteger(type) ? (0, _from_integer.FromInteger)(context, type) :
    T.IsIntersect(type) ? (0, _from_intersect.FromIntersect)(context, type) :
    T.IsIterator(type) ? (0, _from_iterator.FromIterator)(context, type) :
    T.IsLiteral(type) ? (0, _from_literal.FromLiteral)(context, type) :
    T.IsNever(type) ? (0, _from_never.FromNever)(context, type) :
    T.IsNull(type) ? (0, _from_null.FromNull)(context, type) :
    T.IsNumber(type) ? (0, _from_number.FromNumber)(context, type) :
    T.IsObject(type) ? (0, _from_object.FromObject)(context, type) :
    T.IsPromise(type) ? (0, _from_promise.FromPromise)(context, type) :
    T.IsRecord(type) ? (0, _from_record.FromRecord)(context, type) :
    T.IsRef(type) ? (0, _from_ref.FromRef)(context, type) :
    T.IsString(type) ? (0, _from_string.FromString)(context, type) :
    T.IsSymbol(type) ? (0, _from_symbol.FromSymbol)(context, type) :
    T.IsTemplateLiteral(type) ? (0, _from_template_literal.FromTemplateLiteral)(context, type) :
    T.IsTuple(type) ? (0, _from_tuple.FromTuple)(context, type) :
    T.IsUndefined(type) ? (0, _from_undefined.FromUndefined)(context, type) :
    T.IsUnion(type) ? (0, _from_union.FromUnion)(context, type) :
    T.IsVoid(type) ? (0, _from_void.FromVoid)(context, type) :
    undefined);
} /* v9-f08e7b2f0df4d753 */
