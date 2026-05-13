"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildRefine = BuildRefine;exports.CheckRefine = CheckRefine;exports.ErrorRefine = ErrorRefine;
var V = _interopRequireWildcard(require("./_externals.mjs"));
var _index = require("../../guard/index.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildRefine(_stack, _context, schema, value) {
  const refinements = V.CreateVariable(schema['~refine'].map((refinement) => refinement));
  return _index.EmitGuard.Every(refinements, _index.EmitGuard.Constant(0), ['refinement', '_'], _index.EmitGuard.Call(_index.EmitGuard.Member('refinement', 'check'), [value]));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckRefine(_stack, _context, schema, value) {
  return _index.Guard.Every(schema['~refine'], 0, (refinement, _) => refinement.check(value));
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorRefine(_stack, context, schemaPath, instancePath, schema, value) {
  return _index.Guard.EveryAll(schema['~refine'], 0, (refinement, index) => {
    return refinement.check(value) || context.AddError({
      keyword: '~refine',
      schemaPath,
      instancePath,
      params: { index, message: refinement.error(value) }
    });
  });
} /* v9-93f021c27aadf7d2 */
