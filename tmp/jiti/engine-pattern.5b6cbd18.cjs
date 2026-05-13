"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildPattern = BuildPattern;exports.CheckPattern = CheckPattern;exports.ErrorPattern = ErrorPattern;
var Externals = _interopRequireWildcard(require("./_externals.mjs"));
var _index = require("../../guard/index.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildPattern(_stack, _context, schema, value) {
  const regexp = Externals.CreateVariable(_index.Guard.IsString(schema.pattern) ? new RegExp(schema.pattern, 'u') : schema.pattern);
  return _index.EmitGuard.Call(_index.EmitGuard.Member(regexp, 'test'), [value]);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckPattern(_stack, _context, schema, value) {
  const regexp = _index.Guard.IsString(schema.pattern) ? new RegExp(schema.pattern, 'u') : schema.pattern;
  return regexp.test(value);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorPattern(stack, context, schemaPath, instancePath, schema, value) {
  return CheckPattern(stack, context, schema, value) || context.AddError({
    keyword: 'pattern',
    schemaPath,
    instancePath,
    params: { pattern: schema.pattern }
  });
} /* v9-829f15df12e90231 */
