"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildNot = BuildNot;exports.CheckNot = CheckNot;exports.ErrorNot = ErrorNot;
var _context = require("./_context.mjs");
var _reducer = require("./_reducer.mjs");
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildNotUnevaluated(stack, context, schema, value) {
  return (0, _reducer.Reducer)(stack, context, [schema.not], value, _index.EmitGuard.Not(_index.EmitGuard.IsEqual(_index.EmitGuard.Member('results', 'length'), _index.EmitGuard.Constant(1))));
}
function BuildNotFast(stack, context, schema, value) {
  return _index.EmitGuard.Not((0, _schema.BuildSchema)(stack, context, schema.not, value));
}
function BuildNot(stack, context, schema, value) {
  return context.UseUnevaluated() ? BuildNotUnevaluated(stack, context, schema, value) : BuildNotFast(stack, context, schema, value);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckNot(stack, context, schema, value) {
  const nextContext = new _context.CheckContext();
  const isSchema = !(0, _schema.CheckSchema)(stack, nextContext, schema.not, value);
  const isNot = isSchema && context.Merge([nextContext]);
  return isNot;
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorNot(stack, context, schemaPath, instancePath, schema, value) {
  return CheckNot(stack, context, schema, value) || context.AddError({
    keyword: 'not',
    schemaPath,
    instancePath,
    params: {}
  });
} /* v9-bc94d7e0f7e81232 */
