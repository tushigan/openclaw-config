"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildDependentSchemas = BuildDependentSchemas;exports.CheckDependentSchemas = CheckDependentSchemas;exports.ErrorDependentSchemas = ErrorDependentSchemas;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildDependentSchemas(stack, context, schema, value) {
  const isLength = _index.EmitGuard.IsEqual(_index.EmitGuard.Member(_index.EmitGuard.Keys(value), 'length'), _index.EmitGuard.Constant(0));
  const isEvery = _index.EmitGuard.ReduceAnd(_index.Guard.Entries(schema.dependentSchemas).map(([key, schema]) => {
    const notKey = _index.EmitGuard.Not(_index.EmitGuard.HasPropertyKey(value, _index.EmitGuard.Constant(key)));
    const isSchema = (0, _schema.BuildSchema)(stack, context, schema, value);
    return _index.EmitGuard.Or(notKey, isSchema);
  }));
  return _index.EmitGuard.Or(isLength, isEvery);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckDependentSchemas(stack, context, schema, value) {
  const isLength = _index.Guard.IsEqual(_index.Guard.Keys(value).length, 0);
  const isEvery = _index.Guard.Every(_index.Guard.Entries(schema.dependentSchemas), 0, ([key, schema]) => {
    return !_index.Guard.HasPropertyKey(value, key) ||
    (0, _schema.CheckSchema)(stack, context, schema, value);
  });
  return isLength || isEvery;
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorDependentSchemas(stack, context, schemaPath, instancePath, schema, value) {
  const isLength = _index.Guard.IsEqual(_index.Guard.Keys(value).length, 0);
  const isEvery = _index.Guard.EveryAll(_index.Guard.Entries(schema.dependentSchemas), 0, ([key, schema]) => {
    const nextSchemaPath = `${schemaPath}/dependentSchemas/${key}`;
    return !_index.Guard.HasPropertyKey(value, key) ||
    (0, _schema.ErrorSchema)(stack, context, nextSchemaPath, instancePath, schema, value);
  });
  return isLength || isEvery;
} /* v9-077578983ee0d730 */
