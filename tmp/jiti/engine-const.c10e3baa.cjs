"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildConst = BuildConst;exports.CheckConst = CheckConst;exports.ErrorConst = ErrorConst;
var Externals = _interopRequireWildcard(require("./_externals.mjs"));
var _index = require("../../guard/index.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildConst(_stack, _context, schema, value) {
  return _index.Guard.IsValueLike(schema.const) ?
  _index.EmitGuard.IsEqual(value, _index.EmitGuard.Constant(schema.const)) :
  _index.EmitGuard.IsDeepEqual(value, Externals.CreateVariable(schema.const));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckConst(_stack, _context, schema, value) {
  return _index.Guard.IsValueLike(schema.const) ?
  _index.Guard.IsEqual(value, schema.const) :
  _index.Guard.IsDeepEqual(value, schema.const);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function ErrorConst(stack, context, schemaPath, instancePath, schema, value) {
  return CheckConst(stack, context, schema, value) || context.AddError({
    keyword: 'const',
    schemaPath,
    instancePath,
    params: { allowedValue: schema.const }
  });
} /* v9-f4cd51b1b20c4a79 */
