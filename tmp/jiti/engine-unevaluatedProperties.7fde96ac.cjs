"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildUnevaluatedProperties = BuildUnevaluatedProperties;exports.CheckUnevaluatedProperties = CheckUnevaluatedProperties;exports.ErrorUnevaluatedProperties = ErrorUnevaluatedProperties;
var _unique = require("./_unique.mjs");
var _context = require("./_context.mjs");
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildUnevaluatedProperties(stack, context, schema, value) {
  const [key, prop] = [(0, _unique.Unique)(), (0, _unique.Unique)()];
  const keys = _index.EmitGuard.Call(_index.EmitGuard.Member('context', 'GetKeys'), []);
  const hasKey = _index.EmitGuard.Call(_index.EmitGuard.Member('keys', 'has'), [key]);
  const addKey = _index.EmitGuard.Call(_index.EmitGuard.Member('context', 'AddKey'), [key]);
  const isSchema = (0, _schema.BuildSchema)(stack, context, schema.unevaluatedProperties, prop);
  const isEvery = _index.EmitGuard.Every(_index.EmitGuard.Entries(value), _index.EmitGuard.Constant(0), [`[${key}, ${prop}]`, '_'], _index.EmitGuard.Or(hasKey, _index.EmitGuard.And(isSchema, addKey)));
  return _index.EmitGuard.Call(_index.EmitGuard.ArrowFunction(['context'], _index.EmitGuard.Statements([
  _index.EmitGuard.ConstDeclaration('keys', keys),
  _index.EmitGuard.Return(isEvery)]
  )), ['context']);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckUnevaluatedProperties(stack, context, schema, value) {
  const keys = context.GetKeys();
  return _index.Guard.Every(_index.Guard.Entries(value), 0, ([key, prop]) => {
    return keys.has(key) ||
    (0, _schema.CheckSchema)(stack, context, schema.unevaluatedProperties, prop) && context.AddKey(key);
  });
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorUnevaluatedProperties(stack, context, schemaPath, instancePath, schema, value) {
  const keys = context.GetKeys();
  const unevaluatedProperties = [];
  const isUnevaluatedProperties = _index.Guard.EveryAll(_index.Guard.Entries(value), 0, ([key, prop]) => {
    const nextContext = new _context.AccumulatedErrorContext();
    const isEvaluatedProperty = keys.has(key) ||
    (0, _schema.ErrorSchema)(stack, nextContext, schemaPath, instancePath, schema.unevaluatedProperties, prop) && context.AddKey(key);
    if (!isEvaluatedProperty)
    unevaluatedProperties.push(key);
    return isEvaluatedProperty;
  });
  return isUnevaluatedProperties || context.AddError({
    keyword: 'unevaluatedProperties',
    schemaPath,
    instancePath,
    params: { unevaluatedProperties }
  });
} /* v9-743c65457a228250 */
