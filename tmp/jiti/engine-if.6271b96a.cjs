"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildIf = BuildIf;exports.CheckIf = CheckIf;exports.ErrorIf = ErrorIf;
var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _context = require("./_context.mjs");
var _index2 = require("../../guard/index.mjs");
var _schema = require("./schema.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildIf(stack, context, schema, value) {
  const thenSchema = Schema.IsThen(schema) ? schema.then : true;
  const elseSchema = Schema.IsElse(schema) ? schema.else : true;
  return _index2.EmitGuard.Ternary((0, _schema.BuildSchema)(stack, context, schema.if, value), (0, _schema.BuildSchema)(stack, context, thenSchema, value), (0, _schema.BuildSchema)(stack, context, elseSchema, value));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckIf(stack, context, schema, value) {
  const thenSchema = Schema.IsThen(schema) ? schema.then : true;
  const elseSchema = Schema.IsElse(schema) ? schema.else : true;
  return (0, _schema.CheckSchema)(stack, context, schema.if, value) ?
  (0, _schema.CheckSchema)(stack, context, thenSchema, value) :
  (0, _schema.CheckSchema)(stack, context, elseSchema, value);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorIf(stack, context, schemaPath, instancePath, schema, value) {
  const thenSchema = Schema.IsThen(schema) ? schema.then : true;
  const elseSchema = Schema.IsElse(schema) ? schema.else : true;
  const trueContext = new _context.AccumulatedErrorContext();
  const isIf = (0, _schema.ErrorSchema)(stack, trueContext, `${schemaPath}/if`, instancePath, schema.if, value) ?
  (0, _schema.ErrorSchema)(stack, trueContext, `${schemaPath}/then`, instancePath, thenSchema, value) || context.AddError({
    keyword: 'if',
    schemaPath,
    instancePath,
    params: { failingKeyword: 'then' }
  }) :
  (0, _schema.ErrorSchema)(stack, context, `${schemaPath}/else`, instancePath, elseSchema, value) || context.AddError({
    keyword: 'if',
    schemaPath,
    instancePath,
    params: { failingKeyword: 'else' }
  });
  if (isIf)
  context.Merge([trueContext]);
  return isIf;
} /* v9-5152d25d7fea5117 */
