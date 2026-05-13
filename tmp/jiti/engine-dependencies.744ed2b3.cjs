"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildDependencies = BuildDependencies;exports.CheckDependencies = CheckDependencies;exports.ErrorDependencies = ErrorDependencies;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildDependencies(stack, context, schema, value) {
  const isLength = _index.EmitGuard.IsEqual(_index.EmitGuard.Member(_index.EmitGuard.Keys(value), 'length'), _index.EmitGuard.Constant(0));
  const isEveryDependency = _index.EmitGuard.ReduceAnd(_index.Guard.Entries(schema.dependencies).map(([key, schema]) => {
    const notKey = _index.EmitGuard.Not(_index.EmitGuard.HasPropertyKey(value, _index.EmitGuard.Constant(key)));
    const isSchema = (0, _schema.BuildSchema)(stack, context, schema, value);
    const isEveryKey = (schema) => _index.EmitGuard.ReduceAnd(schema.map((key) => _index.EmitGuard.HasPropertyKey(value, _index.EmitGuard.Constant(key))));
    return _index.EmitGuard.Or(notKey, _index.Guard.IsArray(schema) ? isEveryKey(schema) : isSchema);
  }));
  return _index.EmitGuard.Or(isLength, isEveryDependency);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckDependencies(stack, context, schema, value) {
  const isLength = _index.Guard.IsEqual(_index.Guard.Keys(value).length, 0);
  const isEvery = _index.Guard.Every(_index.Guard.Entries(schema.dependencies), 0, ([key, schema]) => {
    return !_index.Guard.HasPropertyKey(value, key) || (_index.Guard.IsArray(schema) ?
    schema.every((key) => _index.Guard.HasPropertyKey(value, key)) :
    (0, _schema.CheckSchema)(stack, context, schema, value));
  });
  return isLength || isEvery;
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorDependencies(stack, context, schemaPath, instancePath, schema, value) {
  const isLength = _index.Guard.IsEqual(_index.Guard.Keys(value).length, 0);
  const isEvery = _index.Guard.EveryAll(_index.Guard.Entries(schema.dependencies), 0, ([key, schema]) => {
    const nextSchemaPath = `${schemaPath}/dependencies/${key}`;
    return !_index.Guard.HasPropertyKey(value, key) || (_index.Guard.IsArray(schema) ?
    schema.every((dependency) => _index.Guard.HasPropertyKey(value, dependency) || context.AddError({
      keyword: 'dependencies',
      schemaPath,
      instancePath,
      params: { property: key, dependencies: schema }
    })) : (0, _schema.ErrorSchema)(stack, context, nextSchemaPath, instancePath, schema, value));
  });
  return isLength || isEvery;
} /* v9-6af11a3fec35ace8 */
