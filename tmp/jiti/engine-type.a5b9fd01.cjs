"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildType = BuildType;exports.CheckType = CheckType;exports.ErrorType = ErrorType;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// TypeName
// ------------------------------------------------------------------
function BuildTypeName(_stack, _context, type, value) {
  return (
    // jsonschema
    _index.Guard.IsEqual(type, 'object') ? _index.EmitGuard.IsObjectNotArray(value) :
    _index.Guard.IsEqual(type, 'array') ? _index.EmitGuard.IsArray(value) :
    _index.Guard.IsEqual(type, 'boolean') ? _index.EmitGuard.IsBoolean(value) :
    _index.Guard.IsEqual(type, 'integer') ? _index.EmitGuard.IsInteger(value) :
    _index.Guard.IsEqual(type, 'number') ? _index.EmitGuard.IsNumber(value) :
    _index.Guard.IsEqual(type, 'null') ? _index.EmitGuard.IsNull(value) :
    _index.Guard.IsEqual(type, 'string') ? _index.EmitGuard.IsString(value) :
    // xschema
    _index.Guard.IsEqual(type, 'asyncIterator') ? _index.EmitGuard.IsAsyncIterator(value) :
    _index.Guard.IsEqual(type, 'bigint') ? _index.EmitGuard.IsBigInt(value) :
    _index.Guard.IsEqual(type, 'constructor') ? _index.EmitGuard.IsConstructor(value) :
    _index.Guard.IsEqual(type, 'function') ? _index.EmitGuard.IsFunction(value) :
    _index.Guard.IsEqual(type, 'iterator') ? _index.EmitGuard.IsIterator(value) :
    _index.Guard.IsEqual(type, 'symbol') ? _index.EmitGuard.IsSymbol(value) :
    _index.Guard.IsEqual(type, 'undefined') ? _index.EmitGuard.IsUndefined(value) :
    _index.Guard.IsEqual(type, 'void') ? _index.EmitGuard.IsUndefined(value) :
    _index.EmitGuard.Constant(true));
}
function CheckTypeName(_stack, _context, type, _schema, value) {
  return (
    // jsonschema
    _index.Guard.IsEqual(type, 'object') ? _index.Guard.IsObjectNotArray(value) :
    _index.Guard.IsEqual(type, 'array') ? _index.Guard.IsArray(value) :
    _index.Guard.IsEqual(type, 'boolean') ? _index.Guard.IsBoolean(value) :
    _index.Guard.IsEqual(type, 'integer') ? _index.Guard.IsInteger(value) :
    _index.Guard.IsEqual(type, 'number') ? _index.Guard.IsNumber(value) :
    _index.Guard.IsEqual(type, 'null') ? _index.Guard.IsNull(value) :
    _index.Guard.IsEqual(type, 'string') ? _index.Guard.IsString(value) :
    // xschema
    _index.Guard.IsEqual(type, 'asyncIterator') ? _index.Guard.IsAsyncIterator(value) :
    _index.Guard.IsEqual(type, 'bigint') ? _index.Guard.IsBigInt(value) :
    _index.Guard.IsEqual(type, 'constructor') ? _index.Guard.IsConstructor(value) :
    _index.Guard.IsEqual(type, 'function') ? _index.Guard.IsFunction(value) :
    _index.Guard.IsEqual(type, 'iterator') ? _index.Guard.IsIterator(value) :
    _index.Guard.IsEqual(type, 'symbol') ? _index.Guard.IsSymbol(value) :
    _index.Guard.IsEqual(type, 'undefined') ? _index.Guard.IsUndefined(value) :
    _index.Guard.IsEqual(type, 'void') ? _index.Guard.IsUndefined(value) :
    true);
}
// ------------------------------------------------------------------
// TypeNames
// ------------------------------------------------------------------
function BuildTypeNames(stack, context, typenames, value) {
  return _index.EmitGuard.ReduceOr(typenames.map((type) => BuildTypeName(stack, context, type, value)));
}
function CheckTypeNames(stack, context, types, schema, value) {
  return types.some((type) => CheckTypeName(stack, context, type, schema, value));
}
// ------------------------------------------------------------------
// Type
// ------------------------------------------------------------------
function BuildType(stack, context, schema, value) {
  return _index.Guard.IsArray(schema.type) ? BuildTypeNames(stack, context, schema.type, value) : BuildTypeName(stack, context, schema.type, value);
}
function CheckType(stack, context, schema, value) {
  return _index.Guard.IsArray(schema.type) ? CheckTypeNames(stack, context, schema.type, schema, value) : CheckTypeName(stack, context, schema.type, schema, value);
}
function ErrorType(stack, context, schemaPath, instancePath, schema, value) {
  const isType = _index.Guard.IsArray(schema.type) ? CheckTypeNames(stack, context, schema.type, schema, value) : CheckTypeName(stack, context, schema.type, schema, value);
  return isType || context.AddError({
    keyword: 'type',
    schemaPath,
    instancePath,
    params: { type: schema.type }
  });
} /* v9-b8692d6145395ac9 */
