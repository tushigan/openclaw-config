"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildAnyOf = BuildAnyOf;exports.CheckAnyOf = CheckAnyOf;exports.ErrorAnyOf = ErrorAnyOf;
var _context = require("./_context.mjs");
var _reducer = require("./_reducer.mjs");
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildAnyOfStandard(stack, context, schema, value) {
  return (0, _reducer.Reducer)(stack, context, schema.anyOf, value, _index.EmitGuard.IsGreaterThan(_index.EmitGuard.Member('results', 'length'), _index.EmitGuard.Constant(0)));
}
function BuildAnyOfFast(stack, context, schema, value) {
  return _index.EmitGuard.ReduceOr(schema.anyOf.map((schema) => (0, _schema.BuildSchema)(stack, context, schema, value)));
}
function BuildAnyOf(stack, context, schema, value) {
  return context.UseUnevaluated() ?
  BuildAnyOfStandard(stack, context, schema, value) :
  BuildAnyOfFast(stack, context, schema, value);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckAnyOf(stack, context, schema, value) {
  const results = schema.anyOf.reduce((result, schema) => {
    const nextContext = new _context.CheckContext();
    return (0, _schema.CheckSchema)(stack, nextContext, schema, value) ? [...result, nextContext] : result;
  }, []);
  return _index.Guard.IsGreaterThan(results.length, 0) && context.Merge(results);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorAnyOf(stack, context, schemaPath, instancePath, schema, value) {
  const failedContexts = [];
  const results = schema.anyOf.reduce((result, schema, index) => {
    const nextContext = new _context.AccumulatedErrorContext();
    const nextSchemaPath = `${schemaPath}/anyOf/${index}`;
    const isSchema = (0, _schema.ErrorSchema)(stack, nextContext, nextSchemaPath, instancePath, schema, value);
    if (!isSchema)
    failedContexts.push(nextContext);
    return isSchema ? [...result, nextContext] : result;
  }, []);
  const isAnyOf = _index.Guard.IsGreaterThan(results.length, 0) && context.Merge(results);
  if (!isAnyOf)
  failedContexts.forEach((failed) => failed.GetErrors().forEach((error) => context.AddError(error)));
  return isAnyOf || context.AddError({
    keyword: 'anyOf',
    schemaPath,
    instancePath,
    params: {}
  });
} /* v9-6c5edb87c44b8daa */
