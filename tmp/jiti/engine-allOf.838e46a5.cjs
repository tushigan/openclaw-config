"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildAllOf = BuildAllOf;exports.CheckAllOf = CheckAllOf;exports.ErrorAllOf = ErrorAllOf;
var _context = require("./_context.mjs");
var _reducer = require("./_reducer.mjs");
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildAllOfStandard(stack, context, schema, value) {
  return (0, _reducer.Reducer)(stack, context, schema.allOf, value, _index.EmitGuard.IsEqual(_index.EmitGuard.Member('results', 'length'), _index.EmitGuard.Constant(schema.allOf.length)));
}
function BuildAllOfFast(stack, context, schema, value) {
  return _index.EmitGuard.ReduceAnd(schema.allOf.map((schema) => (0, _schema.BuildSchema)(stack, context, schema, value)));
}
function BuildAllOf(stack, context, schema, value) {
  return context.UseUnevaluated() ?
  BuildAllOfStandard(stack, context, schema, value) :
  BuildAllOfFast(stack, context, schema, value);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckAllOf(stack, context, schema, value) {
  const results = schema.allOf.reduce((result, schema) => {
    const nextContext = new _context.CheckContext();
    return (0, _schema.CheckSchema)(stack, nextContext, schema, value) ? [...result, nextContext] : result;
  }, []);
  return _index.Guard.IsEqual(results.length, schema.allOf.length) && context.Merge(results);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorAllOf(stack, context, schemaPath, instancePath, schema, value) {
  const failedContexts = [];
  const results = schema.allOf.reduce((result, schema, index) => {
    const nextSchemaPath = `${schemaPath}/allOf/${index}`;
    const nextContext = new _context.AccumulatedErrorContext();
    const isSchema = (0, _schema.ErrorSchema)(stack, nextContext, nextSchemaPath, instancePath, schema, value);
    if (!isSchema)
    failedContexts.push(nextContext);
    return isSchema ? [...result, nextContext] : result;
  }, []);
  const isAllOf = _index.Guard.IsEqual(results.length, schema.allOf.length) && context.Merge(results);
  if (!isAllOf)
  failedContexts.forEach((failed) => failed.GetErrors().forEach((error) => context.AddError(error)));
  return isAllOf;
} /* v9-75ae96f2aeab8829 */
