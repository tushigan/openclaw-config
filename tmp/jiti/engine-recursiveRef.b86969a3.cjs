"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildRecursiveRef = BuildRecursiveRef;exports.CheckRecursiveRef = CheckRecursiveRef;exports.ErrorRecursiveRef = ErrorRecursiveRef;
var Functions = _interopRequireWildcard(require("./_functions.mjs"));
var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _schema = require("./schema.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildRecursiveRef(stack, context, schema, value) {
  const target = stack.RecursiveRef(schema) ?? false;
  return Functions.CreateFunction(stack, context, target, value);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckRecursiveRef(stack, context, schema, value) {
  const target = stack.RecursiveRef(schema) ?? false;
  return Schema.IsSchema(target) && (0, _schema.CheckSchema)(stack, context, target, value);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorRecursiveRef(stack, context, _schemaPath, instancePath, schema, value) {
  const target = stack.RecursiveRef(schema) ?? false;
  return Schema.IsSchema(target) && (0, _schema.ErrorSchema)(stack, context, '#', instancePath, target, value);
} /* v9-f2ce9d27e30c0f62 */
