"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildContains = BuildContains;exports.CheckContains = CheckContains;exports.ErrorContains = ErrorContains;
var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _unique = require("./_unique.mjs");
var _index2 = require("../../guard/index.mjs");
var _schema = require("./schema.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Invalid
// ------------------------------------------------------------------
function IsValid(schema) {
  return !(Schema.IsMinContains(schema) && _index2.Guard.IsEqual(schema.minContains, 0));
}
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildContains(stack, context, schema, value) {
  if (!IsValid(schema))
  return _index2.EmitGuard.Constant(true);
  const item = (0, _unique.Unique)();
  const isLength = _index2.EmitGuard.Not(_index2.EmitGuard.IsEqual(_index2.EmitGuard.Member(value, 'length'), _index2.EmitGuard.Constant(0)));
  const isSome = _index2.EmitGuard.Call(_index2.EmitGuard.Member(value, 'some'), [_index2.EmitGuard.ArrowFunction([item], (0, _schema.BuildSchema)(stack, context, schema.contains, item))]);
  return _index2.EmitGuard.And(isLength, isSome);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckContains(stack, context, schema, value) {
  if (!IsValid(schema))
  return true;
  return !_index2.Guard.IsEqual(value.length, 0) &&
  value.some((item) => (0, _schema.CheckSchema)(stack, context, schema.contains, item));
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorContains(stack, context, schemaPath, instancePath, schema, value) {
  return CheckContains(stack, context, schema, value) || context.AddError({
    keyword: 'contains',
    schemaPath,
    instancePath,
    params: { minContains: 1 }
  });
} /* v9-2586e3cad1c971f5 */
