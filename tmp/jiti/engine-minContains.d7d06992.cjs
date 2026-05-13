"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildMinContains = BuildMinContains;exports.CheckMinContains = CheckMinContains;exports.ErrorMinContains = ErrorMinContains;
var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _unique = require("./_unique.mjs");
var _index2 = require("../../guard/index.mjs");
var _schema = require("./schema.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Valid
// ------------------------------------------------------------------
function IsValid(schema) {
  return Schema.IsContains(schema);
}
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildMinContains(stack, context, schema, value) {
  if (!IsValid(schema))
  return _index2.EmitGuard.Constant(true);
  const [result, item] = [(0, _unique.Unique)(), (0, _unique.Unique)()];
  const count = _index2.EmitGuard.Call(_index2.EmitGuard.Member(value, 'reduce'), [_index2.EmitGuard.ArrowFunction([result, item], _index2.EmitGuard.Ternary((0, _schema.BuildSchema)(stack, context, schema.contains, item), _index2.EmitGuard.PrefixIncrement(result), result)), _index2.EmitGuard.Constant(0)]);
  return _index2.EmitGuard.IsGreaterEqualThan(count, _index2.EmitGuard.Constant(schema.minContains));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckMinContains(stack, context, schema, value) {
  if (!IsValid(schema))
  return true;
  const count = value.reduce((result, item) => (0, _schema.CheckSchema)(stack, context, schema.contains, item) ? ++result : result, 0);
  return _index2.Guard.IsGreaterEqualThan(count, schema.minContains);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorMinContains(stack, context, schemaPath, instancePath, schema, value) {
  return CheckMinContains(stack, context, schema, value) || context.AddError({
    keyword: 'contains',
    schemaPath,
    instancePath,
    params: { minContains: schema.minContains }
  });
} /* v9-e18b099017848514 */
