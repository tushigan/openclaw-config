"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.CreateFunction = CreateFunction;exports.GetFunctions = GetFunctions;exports.ResetFunctions = ResetFunctions;
var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _index2 = require("../../system/hashing/index.mjs");
var _index3 = require("../../guard/index.mjs");
var _schema2 = require("./schema.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
const functions = new Map();
// ------------------------------------------------------------------
// CreateCallExpression
// ------------------------------------------------------------------
function CreateCallExpression(context, _schema, hash, value) {
  return context.UseUnevaluated() ?
  _index3.EmitGuard.Call(`check_${hash}`, ['context', value]) :
  _index3.EmitGuard.Call(`check_${hash}`, [value]);
}
// ------------------------------------------------------------------
// CreateFunctionExpression
// ------------------------------------------------------------------
function CreateFunctionExpression(stack, context, schema, hash) {
  const expression = (0, _schema2.BuildSchema)(stack, context, schema, 'value');
  return context.UseUnevaluated() ?
  _index3.EmitGuard.ConstDeclaration(`check_${hash}`, _index3.EmitGuard.ArrowFunction(['context', 'value'], expression)) :
  _index3.EmitGuard.ConstDeclaration(`check_${hash}`, _index3.EmitGuard.ArrowFunction(['value'], expression));
}
// ------------------------------------------------------------------
// ResetFunctions
// ------------------------------------------------------------------
function ResetFunctions() {
  functions.clear();
}
// ------------------------------------------------------------------
// GetFunctions
// ------------------------------------------------------------------
function GetFunctions() {
  return [...functions.values()];
}
// ------------------------------------------------------------------
// CreateFunction
// ------------------------------------------------------------------
function CreateFunction(stack, context, schema, value) {
  const hash = Schema.IsSchemaObject(schema) ? _index2.Hashing.Hash({ __baseURL: stack.BaseURL().href, ...schema }) : _index2.Hashing.Hash(schema);
  const call = CreateCallExpression(context, schema, hash, value);
  if (functions.has(hash))
  return call;
  functions.set(hash, '');
  functions.set(hash, CreateFunctionExpression(stack, context, schema, hash));
  return call;
} /* v9-180b4eb852cc4a7a */
