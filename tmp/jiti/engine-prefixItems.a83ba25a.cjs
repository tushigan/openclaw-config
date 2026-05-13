"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildPrefixItems = BuildPrefixItems;exports.CheckPrefixItems = CheckPrefixItems;exports.ErrorPrefixItems = ErrorPrefixItems;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildPrefixItems(stack, context, schema, value) {
  return _index.EmitGuard.ReduceAnd(schema.prefixItems.map((schema, index) => {
    const isLength = _index.EmitGuard.IsLessEqualThan(_index.EmitGuard.Member(value, 'length'), _index.EmitGuard.Constant(index));
    const isSchema = (0, _schema.BuildSchemaPushStack)(stack, context, schema, `${value}[${index}]`);
    const addIndex = context.AddIndex(_index.EmitGuard.Constant(index));
    const guarded = context.UseUnevaluated() ? _index.EmitGuard.And(isSchema, addIndex) : isSchema;
    return _index.EmitGuard.Or(isLength, guarded);
  }));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckPrefixItems(stack, context, schema, value) {
  return _index.Guard.IsEqual(value.length, 0) || _index.Guard.Every(schema.prefixItems, 0, (schema, index) => {
    return _index.Guard.IsLessEqualThan(value.length, index) ||
    (0, _schema.CheckSchemaPushStack)(stack, context, schema, value[index]) && context.AddIndex(index);
  });
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorPrefixItems(stack, context, schemaPath, instancePath, schema, value) {
  return _index.Guard.IsEqual(value.length, 0) || _index.Guard.EveryAll(schema.prefixItems, 0, (schema, index) => {
    const nextSchemaPath = `${schemaPath}/prefixItems/${index}`;
    const nextInstancePath = `${instancePath}/${index}`;
    return _index.Guard.IsLessEqualThan(value.length, index) ||
    (0, _schema.ErrorSchemaPushStack)(stack, context, nextSchemaPath, nextInstancePath, schema, value[index]) && context.AddIndex(index);
  });
} /* v9-7e85c39678e45639 */
