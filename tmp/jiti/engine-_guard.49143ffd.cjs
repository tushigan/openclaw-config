"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildGuard = BuildGuard;exports.CheckGuard = CheckGuard;exports.ErrorGuard = ErrorGuard;
var Externals = _interopRequireWildcard(require("./_externals.mjs"));
var _index = require("../../guard/index.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildGuard(_stack, _context, schema, value) {
  return _index.EmitGuard.Call(_index.EmitGuard.Member(_index.EmitGuard.Member(Externals.CreateVariable(schema), '~guard'), 'check'), [value]);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckGuard(_stack, _context, schema, value) {
  return schema['~guard'].check(value);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorGuard(_stack, context, schemaPath, instancePath, schema, value) {
  return schema['~guard'].check(value) || context.AddError({
    keyword: '~guard',
    schemaPath,
    instancePath,
    params: { errors: schema['~guard'].errors(value) }
  });
} /* v9-4b948350e7fac373 */
