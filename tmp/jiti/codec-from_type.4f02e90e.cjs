"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromType = FromType;
var Type = _interopRequireWildcard(require("../../type/index.mjs"));
var _from_array = require("./from_array.mjs");
var _from_cyclic = require("./from_cyclic.mjs");
var _from_intersect = require("./from_intersect.mjs");
var _from_object = require("./from_object.mjs");
var _from_record = require("./from_record.mjs");
var _from_ref = require("./from_ref.mjs");
var _from_tuple = require("./from_tuple.mjs");
var _from_union = require("./from_union.mjs");
var _callback = require("./callback.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
function FromType(direction, context, type, value) {
  return Type.IsArray(type) ? (0, _from_array.FromArray)(direction, context, type, value) :
  Type.IsCyclic(type) ? (0, _from_cyclic.FromCyclic)(direction, context, type, value) :
  Type.IsIntersect(type) ? (0, _from_intersect.FromIntersect)(direction, context, type, value) :
  Type.IsObject(type) ? (0, _from_object.FromObject)(direction, context, type, value) :
  Type.IsRecord(type) ? (0, _from_record.FromRecord)(direction, context, type, value) :
  Type.IsRef(type) ? (0, _from_ref.FromRef)(direction, context, type, value) :
  Type.IsTuple(type) ? (0, _from_tuple.FromTuple)(direction, context, type, value) :
  Type.IsUnion(type) ? (0, _from_union.FromUnion)(direction, context, type, value) :
  (0, _callback.Callback)(direction, context, type, value);
} /* v9-518d80714f4eda65 */
