"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildRef = BuildRef;exports.CheckRef = CheckRef;exports.ErrorRef = ErrorRef;
var Functions = _interopRequireWildcard(require("./_functions.mjs"));
var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _context = require("./_context.mjs");
var _index2 = require("../../guard/index.mjs");
var _schema = require("./schema.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// BuildRefStandard
// ------------------------------------------------------------------
function BuildRefStandard(stack, context, target, value) {
  const interior = _index2.EmitGuard.ArrowFunction(['context', 'value'], Functions.CreateFunction(stack, context, target, 'value'));
  const exterior = _index2.EmitGuard.ArrowFunction(['context', 'value'], _index2.EmitGuard.Statements([
  _index2.EmitGuard.ConstDeclaration('nextContext', _index2.EmitGuard.New('CheckContext', [])),
  _index2.EmitGuard.ConstDeclaration('result', _index2.EmitGuard.Call(interior, ['nextContext', 'value'])),
  _index2.EmitGuard.If('result', context.Merge('[nextContext]')),
  _index2.EmitGuard.Return('result')]
  ));
  return _index2.EmitGuard.Call(exterior, ['context', value]);
}
// ------------------------------------------------------------------
// BuildRefStandard
// ------------------------------------------------------------------
function BuildRefFast(stack, context, target, value) {
  return Functions.CreateFunction(stack, context, target, value);
}
// ------------------------------------------------------------------
// BuildRef
// ------------------------------------------------------------------
function BuildRef(stack, context, schema, value) {
  const target = stack.Ref(schema) ?? false;
  return context.UseUnevaluated() ?
  BuildRefStandard(stack, context, target, value) :
  BuildRefFast(stack, context, target, value);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckRef(stack, context, schema, value) {
  const target = stack.Ref(schema) ?? false;
  const nextContext = new _context.CheckContext();
  const result = Schema.IsSchema(target) && (0, _schema.CheckSchema)(stack, nextContext, target, value);
  if (result)
  context.Merge([nextContext]);
  return result;
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorRef(stack, context, _schemaPath, instancePath, schema, value) {
  const target = stack.Ref(schema) ?? false;
  const nextContext = new _context.AccumulatedErrorContext();
  const result = Schema.IsSchema(target) && (0, _schema.ErrorSchema)(stack, nextContext, '#', instancePath, target, value);
  if (result)
  context.Merge([nextContext]);
  if (!result)
  nextContext.GetErrors().forEach((error) => context.AddError(error));
  return result;
} /* v9-90c97826f5036fbb */
