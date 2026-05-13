"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildEnum = BuildEnum;exports.CheckEnum = CheckEnum;exports.ErrorEnum = ErrorEnum;
var Externals = _interopRequireWildcard(require("./_externals.mjs"));
var _index = require("../../guard/index.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildEnum(_stack, _context, schema, value) {
  return _index.EmitGuard.ReduceOr(schema.enum.map((option) => {
    if (_index.Guard.IsValueLike(option))
    return _index.EmitGuard.IsEqual(value, _index.EmitGuard.Constant(option));
    const variable = Externals.CreateVariable(option);
    return _index.EmitGuard.IsDeepEqual(value, variable);
  }));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckEnum(_stack, _context, schema, value) {
  return schema.enum.some((option) => _index.Guard.IsValueLike(option) ?
  _index.Guard.IsEqual(value, option) :
  _index.Guard.IsDeepEqual(value, option));
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorEnum(stack, context, schemaPath, instancePath, schema, value) {
  return CheckEnum(stack, context, schema, value) || context.AddError({
    keyword: 'enum',
    schemaPath,
    instancePath,
    params: { allowedValues: schema.enum }
  });
} /* v9-f1603dad1081ff07 */
