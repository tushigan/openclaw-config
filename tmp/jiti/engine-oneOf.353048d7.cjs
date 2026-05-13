"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildOneOf = BuildOneOf;exports.CheckOneOf = CheckOneOf;exports.ErrorOneOf = ErrorOneOf;
var _context = require("./_context.mjs");
var _reducer = require("./_reducer.mjs");
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildOneOfUnevaluated(stack, context, schema, value) {
  return (0, _reducer.Reducer)(stack, context, schema.oneOf, value, _index.EmitGuard.IsEqual(_index.EmitGuard.Member('results', 'length'), _index.EmitGuard.Constant(1)));
}
function BuildOneOfFast(stack, context, schema, value) {
  const results = _index.EmitGuard.ArrayLiteral(schema.oneOf.map((schema) => (0, _schema.BuildSchema)(stack, context, schema, value)));
  const count = _index.EmitGuard.Call(_index.EmitGuard.Member(results, 'reduce'), [
  _index.EmitGuard.ArrowFunction(['count', 'result'], _index.EmitGuard.Ternary(_index.EmitGuard.IsEqual('result', _index.EmitGuard.Constant(true)), _index.EmitGuard.PrefixIncrement('count'), 'count')),
  _index.EmitGuard.Constant(0)]
  );
  return _index.EmitGuard.IsEqual(count, _index.EmitGuard.Constant(1));
}
function BuildOneOf(stack, context, schema, value) {
  return context.UseUnevaluated() ? BuildOneOfUnevaluated(stack, context, schema, value) : BuildOneOfFast(stack, context, schema, value);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckOneOf(stack, context, schema, value) {
  const passedContexts = schema.oneOf.reduce((result, schema) => {
    const nextContext = new _context.CheckContext();
    return (0, _schema.CheckSchema)(stack, nextContext, schema, value) ? [...result, nextContext] : result;
  }, []);
  return _index.Guard.IsEqual(passedContexts.length, 1) && context.Merge(passedContexts);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorOneOf(stack, context, schemaPath, instancePath, schema, value) {
  const failedContexts = [];
  const passingSchemas = [];
  const passedContexts = schema.oneOf.reduce((result, schema, index) => {
    const nextContext = new _context.AccumulatedErrorContext();
    const nextSchemaPath = `${schemaPath}/oneOf/${index}`;
    const isSchema = (0, _schema.ErrorSchema)(stack, nextContext, nextSchemaPath, instancePath, schema, value);
    if (isSchema)
    passingSchemas.push(index);
    if (!isSchema)
    failedContexts.push(nextContext);
    return isSchema ? [...result, nextContext] : result;
  }, []);
  const isOneOf = _index.Guard.IsEqual(passedContexts.length, 1) && context.Merge(passedContexts);
  if (!isOneOf && _index.Guard.IsEqual(passingSchemas.length, 0))
  failedContexts.forEach((failed) => failed.GetErrors().forEach((error) => context.AddError(error)));
  return isOneOf || context.AddError({
    keyword: 'oneOf',
    schemaPath,
    instancePath,
    params: { passingSchemas }
  });
} /* v9-c2338f21b3a7ad7e */
