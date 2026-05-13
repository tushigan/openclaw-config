"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildSchema = BuildSchema;exports.BuildSchemaPushStack = BuildSchemaPushStack;exports.CheckSchema = CheckSchema;exports.CheckSchemaPushStack = CheckSchemaPushStack;exports.ErrorSchema = ErrorSchema;exports.ErrorSchemaPushStack = ErrorSchemaPushStack;
var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _refine = require("./_refine.mjs");
var _guard = require("./_guard.mjs");
var _index2 = require("../../guard/index.mjs");
var _additionalItems = require("./additionalItems.mjs");
var _additionalProperties = require("./additionalProperties.mjs");
var _allOf = require("./allOf.mjs");
var _anyOf = require("./anyOf.mjs");
var _boolean = require("./boolean.mjs");
var _const = require("./const.mjs");
var _contains = require("./contains.mjs");
var _dependencies = require("./dependencies.mjs");
var _dependentRequired = require("./dependentRequired.mjs");
var _dependentSchemas = require("./dependentSchemas.mjs");
var _dynamicRef = require("./dynamicRef.mjs");
var _enum = require("./enum.mjs");
var _exclusiveMaximum = require("./exclusiveMaximum.mjs");
var _exclusiveMinimum = require("./exclusiveMinimum.mjs");
var _format = require("./format.mjs");
var _if = require("./if.mjs");
var _items = require("./items.mjs");
var _maxContains = require("./maxContains.mjs");
var _maximum = require("./maximum.mjs");
var _maxItems = require("./maxItems.mjs");
var _maxLength = require("./maxLength.mjs");
var _maxProperties = require("./maxProperties.mjs");
var _minContains = require("./minContains.mjs");
var _minimum = require("./minimum.mjs");
var _minItems = require("./minItems.mjs");
var _minLength = require("./minLength.mjs");
var _minProperties = require("./minProperties.mjs");
var _multipleOf = require("./multipleOf.mjs");
var _not = require("./not.mjs");
var _oneOf = require("./oneOf.mjs");
var _pattern = require("./pattern.mjs");
var _patternProperties = require("./patternProperties.mjs");
var _prefixItems = require("./prefixItems.mjs");
var _properties = require("./properties.mjs");
var _propertyNames = require("./propertyNames.mjs");
var _recursiveRef = require("./recursiveRef.mjs");
var _ref = require("./ref.mjs");
var _required = require("./required.mjs");
var _type = require("./type.mjs");
var _unevaluatedItems = require("./unevaluatedItems.mjs");
var _unevaluatedProperties = require("./unevaluatedProperties.mjs");
var _uniqueItems = require("./uniqueItems.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ----------------------------------------------------------------
// HasTypeName
// ----------------------------------------------------------------
function HasTypeName(schema, typename) {
  return Schema.IsType(schema) && (
  _index2.Guard.IsArray(schema.type) && schema.type.includes(typename) ||
  _index2.Guard.IsEqual(schema.type, typename));
}
// ----------------------------------------------------------------
// HasObject
// ----------------------------------------------------------------
function HasObjectType(schema) {
  return HasTypeName(schema, 'object');
}
function HasObjectKeywords(schema) {
  return Schema.IsSchemaObject(schema) && (Schema.IsAdditionalProperties(schema) ||
  Schema.IsDependencies(schema) ||
  Schema.IsDependentRequired(schema) ||
  Schema.IsDependentSchemas(schema) ||
  Schema.IsProperties(schema) ||
  Schema.IsPatternProperties(schema) ||
  Schema.IsPropertyNames(schema) ||
  Schema.IsMinProperties(schema) ||
  Schema.IsMaxProperties(schema) ||
  Schema.IsRequired(schema) ||
  Schema.IsUnevaluatedProperties(schema));
}
// ----------------------------------------------------------------
// HasArray
// ----------------------------------------------------------------
function HasArrayType(schema) {
  return HasTypeName(schema, 'array');
}
function HasArrayKeywords(schema) {
  return Schema.IsSchemaObject(schema) && (Schema.IsAdditionalItems(schema) ||
  Schema.IsItems(schema) ||
  Schema.IsContains(schema) ||
  Schema.IsMaxContains(schema) ||
  Schema.IsMaxItems(schema) ||
  Schema.IsMinContains(schema) ||
  Schema.IsMinItems(schema) ||
  Schema.IsPrefixItems(schema) ||
  Schema.IsUnevaluatedItems(schema) ||
  Schema.IsUniqueItems(schema));
}
// ----------------------------------------------------------------
// HasString
// ----------------------------------------------------------------
function HasStringType(schema) {
  return HasTypeName(schema, 'string');
}
function HasStringKeywords(schema) {
  return Schema.IsSchemaObject(schema) && (Schema.IsMinLength(schema) ||
  Schema.IsMaxLength(schema) ||
  Schema.IsFormat(schema) ||
  Schema.IsPattern(schema));
}
// ----------------------------------------------------------------
// HasNumber
// ----------------------------------------------------------------
function HasNumberType(schema) {
  return HasTypeName(schema, 'number') || HasTypeName(schema, 'bigint');
}
function HasNumberKeywords(schema) {
  return Schema.IsSchemaObject(schema) && (Schema.IsMinimum(schema) ||
  Schema.IsMaximum(schema) ||
  Schema.IsExclusiveMaximum(schema) ||
  Schema.IsExclusiveMinimum(schema) ||
  Schema.IsMultipleOf(schema));
}
// ----------------------------------------------------------------
// Build
// ----------------------------------------------------------------
function BuildSchemaPushStack(stack, context, schema, value) {
  return context.UseUnevaluated() ?
  _index2.EmitGuard.And(_index2.EmitGuard.And(context.Push(), BuildSchema(stack, context, schema, value)), context.Pop()) :
  BuildSchema(stack, context, schema, value);
}
function BuildSchema(stack, context, schema, value) {
  stack.Push(schema);
  const conditions = [];
  if (Schema.IsBooleanSchema(schema))
  return (0, _boolean.BuildBooleanSchema)(stack, context, schema, value);
  if (Schema.IsType(schema))
  conditions.push((0, _type.BuildType)(stack, context, schema, value));
  if (HasObjectKeywords(schema)) {
    const constraints = [];
    if (Schema.IsRequired(schema))
    constraints.push((0, _required.BuildRequired)(stack, context, schema, value));
    if (Schema.IsAdditionalProperties(schema))
    constraints.push((0, _additionalProperties.BuildAdditionalProperties)(stack, context, schema, value));
    if (Schema.IsDependencies(schema))
    constraints.push((0, _dependencies.BuildDependencies)(stack, context, schema, value));
    if (Schema.IsDependentRequired(schema))
    constraints.push((0, _dependentRequired.BuildDependentRequired)(stack, context, schema, value));
    if (Schema.IsDependentSchemas(schema))
    constraints.push((0, _dependentSchemas.BuildDependentSchemas)(stack, context, schema, value));
    if (Schema.IsPatternProperties(schema))
    constraints.push((0, _patternProperties.BuildPatternProperties)(stack, context, schema, value));
    if (Schema.IsProperties(schema))
    constraints.push((0, _properties.BuildProperties)(stack, context, schema, value));
    if (Schema.IsPropertyNames(schema))
    constraints.push((0, _propertyNames.BuildPropertyNames)(stack, context, schema, value));
    if (Schema.IsMinProperties(schema))
    constraints.push((0, _minProperties.BuildMinProperties)(stack, context, schema, value));
    if (Schema.IsMaxProperties(schema))
    constraints.push((0, _maxProperties.BuildMaxProperties)(stack, context, schema, value));
    const reduced = _index2.EmitGuard.ReduceAnd(constraints);
    const guarded = _index2.EmitGuard.Or(_index2.EmitGuard.Not(_index2.EmitGuard.IsObjectNotArray(value)), reduced);
    conditions.push(HasObjectType(schema) ? reduced : guarded);
  }
  if (HasArrayKeywords(schema)) {
    const constraints = [];
    if (Schema.IsAdditionalItems(schema))
    constraints.push((0, _additionalItems.BuildAdditionalItems)(stack, context, schema, value));
    if (Schema.IsContains(schema))
    constraints.push((0, _contains.BuildContains)(stack, context, schema, value));
    if (Schema.IsItems(schema))
    constraints.push((0, _items.BuildItems)(stack, context, schema, value));
    if (Schema.IsMaxContains(schema))
    constraints.push((0, _maxContains.BuildMaxContains)(stack, context, schema, value));
    if (Schema.IsMaxItems(schema))
    constraints.push((0, _maxItems.BuildMaxItems)(stack, context, schema, value));
    if (Schema.IsMinContains(schema))
    constraints.push((0, _minContains.BuildMinContains)(stack, context, schema, value));
    if (Schema.IsMinItems(schema))
    constraints.push((0, _minItems.BuildMinItems)(stack, context, schema, value));
    if (Schema.IsPrefixItems(schema))
    constraints.push((0, _prefixItems.BuildPrefixItems)(stack, context, schema, value));
    if (Schema.IsUniqueItems(schema))
    constraints.push((0, _uniqueItems.BuildUniqueItems)(stack, context, schema, value));
    const reduced = _index2.EmitGuard.ReduceAnd(constraints);
    const guarded = _index2.EmitGuard.Or(_index2.EmitGuard.Not(_index2.EmitGuard.IsArray(value)), reduced);
    conditions.push(HasArrayType(schema) ? reduced : guarded);
  }
  if (HasStringKeywords(schema)) {
    const constraints = [];
    if (Schema.IsMaxLength(schema))
    constraints.push((0, _maxLength.BuildMaxLength)(stack, context, schema, value));
    if (Schema.IsMinLength(schema))
    constraints.push((0, _minLength.BuildMinLength)(stack, context, schema, value));
    if (Schema.IsFormat(schema))
    constraints.push((0, _format.BuildFormat)(stack, context, schema, value));
    if (Schema.IsPattern(schema))
    constraints.push((0, _pattern.BuildPattern)(stack, context, schema, value));
    const reduced = _index2.EmitGuard.ReduceAnd(constraints);
    const guarded = _index2.EmitGuard.Or(_index2.EmitGuard.Not(_index2.EmitGuard.IsString(value)), reduced);
    conditions.push(HasStringType(schema) ? reduced : guarded);
  }
  if (HasNumberKeywords(schema)) {
    const constraints = [];
    if (Schema.IsExclusiveMaximum(schema))
    constraints.push((0, _exclusiveMaximum.BuildExclusiveMaximum)(stack, context, schema, value));
    if (Schema.IsExclusiveMinimum(schema))
    constraints.push((0, _exclusiveMinimum.BuildExclusiveMinimum)(stack, context, schema, value));
    if (Schema.IsMaximum(schema))
    constraints.push((0, _maximum.BuildMaximum)(stack, context, schema, value));
    if (Schema.IsMinimum(schema))
    constraints.push((0, _minimum.BuildMinimum)(stack, context, schema, value));
    if (Schema.IsMultipleOf(schema))
    constraints.push((0, _multipleOf.BuildMultipleOf)(stack, context, schema, value));
    const reduced = _index2.EmitGuard.ReduceAnd(constraints);
    const guarded = _index2.EmitGuard.Or(_index2.EmitGuard.Not(_index2.EmitGuard.Or(_index2.EmitGuard.IsNumber(value), _index2.EmitGuard.IsBigInt(value))), reduced);
    conditions.push(HasNumberType(schema) ? reduced : guarded);
  }
  if (Schema.IsRef(schema))
  conditions.push((0, _ref.BuildRef)(stack, context, schema, value));
  if (Schema.IsRecursiveRef(schema))
  conditions.push((0, _recursiveRef.BuildRecursiveRef)(stack, context, schema, value));
  if (Schema.IsDynamicRef(schema))
  conditions.push((0, _dynamicRef.BuildDynamicRef)(stack, context, schema, value));
  if (Schema.IsGuard(schema))
  conditions.push((0, _guard.BuildGuard)(stack, context, schema, value));
  if (Schema.IsConst(schema))
  conditions.push((0, _const.BuildConst)(stack, context, schema, value));
  if (Schema.IsEnum(schema))
  conditions.push((0, _enum.BuildEnum)(stack, context, schema, value));
  if (Schema.IsIf(schema))
  conditions.push((0, _if.BuildIf)(stack, context, schema, value));
  if (Schema.IsNot(schema))
  conditions.push((0, _not.BuildNot)(stack, context, schema, value));
  if (Schema.IsAllOf(schema))
  conditions.push((0, _allOf.BuildAllOf)(stack, context, schema, value));
  if (Schema.IsAnyOf(schema))
  conditions.push((0, _anyOf.BuildAnyOf)(stack, context, schema, value));
  if (Schema.IsOneOf(schema))
  conditions.push((0, _oneOf.BuildOneOf)(stack, context, schema, value));
  if (Schema.IsUnevaluatedItems(schema))
  conditions.push(_index2.EmitGuard.Or(_index2.EmitGuard.Not(_index2.EmitGuard.IsArray(value)), (0, _unevaluatedItems.BuildUnevaluatedItems)(stack, context, schema, value)));
  if (Schema.IsUnevaluatedProperties(schema))
  conditions.push(_index2.EmitGuard.Or(_index2.EmitGuard.Not(_index2.EmitGuard.IsObject(value)), (0, _unevaluatedProperties.BuildUnevaluatedProperties)(stack, context, schema, value)));
  if (Schema.IsRefine(schema))
  conditions.push((0, _refine.BuildRefine)(stack, context, schema, value));
  const result = _index2.EmitGuard.ReduceAnd(conditions);
  stack.Pop(schema);
  return result;
}
// ----------------------------------------------------------------
// Check
// ----------------------------------------------------------------
function CheckSchemaPushStack(stack, context, schema, value) {
  return context.Push() && CheckSchema(stack, context, schema, value) && context.Pop();
}
function CheckSchema(stack, context, schema, value) {
  stack.Push(schema);
  const result = Schema.IsBooleanSchema(schema) ? (0, _boolean.CheckBooleanSchema)(stack, context, schema, value) : (!Schema.IsType(schema) || (0, _type.CheckType)(stack, context, schema, value)) && (
  !(_index2.Guard.IsObject(value) && !_index2.Guard.IsArray(value)) || (!Schema.IsRequired(schema) || (0, _required.CheckRequired)(stack, context, schema, value)) && (
  !Schema.IsAdditionalProperties(schema) || (0, _additionalProperties.CheckAdditionalProperties)(stack, context, schema, value)) && (
  !Schema.IsDependencies(schema) || (0, _dependencies.CheckDependencies)(stack, context, schema, value)) && (
  !Schema.IsDependentRequired(schema) || (0, _dependentRequired.CheckDependentRequired)(stack, context, schema, value)) && (
  !Schema.IsDependentSchemas(schema) || (0, _dependentSchemas.CheckDependentSchemas)(stack, context, schema, value)) && (
  !Schema.IsPatternProperties(schema) || (0, _patternProperties.CheckPatternProperties)(stack, context, schema, value)) && (
  !Schema.IsProperties(schema) || (0, _properties.CheckProperties)(stack, context, schema, value)) && (
  !Schema.IsPropertyNames(schema) || (0, _propertyNames.CheckPropertyNames)(stack, context, schema, value)) && (
  !Schema.IsMinProperties(schema) || (0, _minProperties.CheckMinProperties)(stack, context, schema, value)) && (
  !Schema.IsMaxProperties(schema) || (0, _maxProperties.CheckMaxProperties)(stack, context, schema, value))) && (
  !_index2.Guard.IsArray(value) || (!Schema.IsAdditionalItems(schema) || (0, _additionalItems.CheckAdditionalItems)(stack, context, schema, value)) && (
  !Schema.IsContains(schema) || (0, _contains.CheckContains)(stack, context, schema, value)) && (
  !Schema.IsItems(schema) || (0, _items.CheckItems)(stack, context, schema, value)) && (
  !Schema.IsMaxContains(schema) || (0, _maxContains.CheckMaxContains)(stack, context, schema, value)) && (
  !Schema.IsMaxItems(schema) || (0, _maxItems.CheckMaxItems)(stack, context, schema, value)) && (
  !Schema.IsMinContains(schema) || (0, _minContains.CheckMinContains)(stack, context, schema, value)) && (
  !Schema.IsMinItems(schema) || (0, _minItems.CheckMinItems)(stack, context, schema, value)) && (
  !Schema.IsPrefixItems(schema) || (0, _prefixItems.CheckPrefixItems)(stack, context, schema, value)) && (
  !Schema.IsUniqueItems(schema) || (0, _uniqueItems.CheckUniqueItems)(stack, context, schema, value))) && (
  !_index2.Guard.IsString(value) || (!Schema.IsMaxLength(schema) || (0, _maxLength.CheckMaxLength)(stack, context, schema, value)) && (
  !Schema.IsMinLength(schema) || (0, _minLength.CheckMinLength)(stack, context, schema, value)) && (
  !Schema.IsFormat(schema) || (0, _format.CheckFormat)(stack, context, schema, value)) && (
  !Schema.IsPattern(schema) || (0, _pattern.CheckPattern)(stack, context, schema, value))) && (
  !(_index2.Guard.IsNumber(value) || _index2.Guard.IsBigInt(value)) || (!Schema.IsExclusiveMaximum(schema) || (0, _exclusiveMaximum.CheckExclusiveMaximum)(stack, context, schema, value)) && (
  !Schema.IsExclusiveMinimum(schema) || (0, _exclusiveMinimum.CheckExclusiveMinimum)(stack, context, schema, value)) && (
  !Schema.IsMaximum(schema) || (0, _maximum.CheckMaximum)(stack, context, schema, value)) && (
  !Schema.IsMinimum(schema) || (0, _minimum.CheckMinimum)(stack, context, schema, value)) && (
  !Schema.IsMultipleOf(schema) || (0, _multipleOf.CheckMultipleOf)(stack, context, schema, value))) && (
  !Schema.IsRef(schema) || (0, _ref.CheckRef)(stack, context, schema, value)) && (
  !Schema.IsRecursiveRef(schema) || (0, _recursiveRef.CheckRecursiveRef)(stack, context, schema, value)) && (
  !Schema.IsDynamicRef(schema) || (0, _dynamicRef.CheckDynamicRef)(stack, context, schema, value)) && (
  !Schema.IsGuard(schema) || (0, _guard.CheckGuard)(stack, context, schema, value)) && (
  !Schema.IsConst(schema) || (0, _const.CheckConst)(stack, context, schema, value)) && (
  !Schema.IsEnum(schema) || (0, _enum.CheckEnum)(stack, context, schema, value)) && (
  !Schema.IsIf(schema) || (0, _if.CheckIf)(stack, context, schema, value)) && (
  !Schema.IsNot(schema) || (0, _not.CheckNot)(stack, context, schema, value)) && (
  !Schema.IsAllOf(schema) || (0, _allOf.CheckAllOf)(stack, context, schema, value)) && (
  !Schema.IsAnyOf(schema) || (0, _anyOf.CheckAnyOf)(stack, context, schema, value)) && (
  !Schema.IsOneOf(schema) || (0, _oneOf.CheckOneOf)(stack, context, schema, value)) && (
  !Schema.IsUnevaluatedItems(schema) || !_index2.Guard.IsArray(value) || (0, _unevaluatedItems.CheckUnevaluatedItems)(stack, context, schema, value)) && (
  !Schema.IsUnevaluatedProperties(schema) || !_index2.Guard.IsObject(value) || (0, _unevaluatedProperties.CheckUnevaluatedProperties)(stack, context, schema, value)) && (
  !Schema.IsRefine(schema) || (0, _refine.CheckRefine)(stack, context, schema, value));
  stack.Pop(schema);
  return result;
}
// ----------------------------------------------------------------
// Error
// ----------------------------------------------------------------
function ErrorSchemaPushStack(stack, context, schemaPath, instancePath, schema, value) {
  return context.Push() && ErrorSchema(stack, context, schemaPath, instancePath, schema, value) && context.Pop();
}
function ErrorSchema(stack, context, schemaPath, instancePath, schema, value) {
  stack.Push(schema);
  const result = Schema.IsBooleanSchema(schema) ? (0, _boolean.ErrorBooleanSchema)(stack, context, schemaPath, instancePath, schema, value) : !!(+(!Schema.IsType(schema) || (0, _type.ErrorType)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!(_index2.Guard.IsObject(value) && !_index2.Guard.IsArray(value)) || !!(+(!Schema.IsRequired(schema) || (0, _required.ErrorRequired)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsAdditionalProperties(schema) || (0, _additionalProperties.ErrorAdditionalProperties)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsDependencies(schema) || (0, _dependencies.ErrorDependencies)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsDependentRequired(schema) || (0, _dependentRequired.ErrorDependentRequired)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsDependentSchemas(schema) || (0, _dependentSchemas.ErrorDependentSchemas)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsPatternProperties(schema) || (0, _patternProperties.ErrorPatternProperties)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsProperties(schema) || (0, _properties.ErrorProperties)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsPropertyNames(schema) || (0, _propertyNames.ErrorPropertyNames)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsMinProperties(schema) || (0, _minProperties.ErrorMinProperties)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsMaxProperties(schema) || (0, _maxProperties.ErrorMaxProperties)(stack, context, schemaPath, instancePath, schema, value)))) &
  +(!_index2.Guard.IsArray(value) || !!(+(!Schema.IsAdditionalItems(schema) || (0, _additionalItems.ErrorAdditionalItems)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsContains(schema) || (0, _contains.ErrorContains)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsItems(schema) || (0, _items.ErrorItems)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsMaxContains(schema) || (0, _maxContains.ErrorMaxContains)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsMaxItems(schema) || (0, _maxItems.ErrorMaxItems)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsMinContains(schema) || (0, _minContains.ErrorMinContains)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsMinItems(schema) || (0, _minItems.ErrorMinItems)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsPrefixItems(schema) || (0, _prefixItems.ErrorPrefixItems)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsUniqueItems(schema) || (0, _uniqueItems.ErrorUniqueItems)(stack, context, schemaPath, instancePath, schema, value)))) &
  +(!_index2.Guard.IsString(value) || !!(+(!Schema.IsMaxLength(schema) || (0, _maxLength.ErrorMaxLength)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsMinLength(schema) || (0, _minLength.ErrorMinLength)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsFormat(schema) || (0, _format.ErrorFormat)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsPattern(schema) || (0, _pattern.ErrorPattern)(stack, context, schemaPath, instancePath, schema, value)))) &
  +(!(_index2.Guard.IsNumber(value) || _index2.Guard.IsBigInt(value)) || !!(+(!Schema.IsExclusiveMaximum(schema) || (0, _exclusiveMaximum.ErrorExclusiveMaximum)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsExclusiveMinimum(schema) || (0, _exclusiveMinimum.ErrorExclusiveMinimum)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsMaximum(schema) || (0, _maximum.ErrorMaximum)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsMinimum(schema) || (0, _minimum.ErrorMinimum)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsMultipleOf(schema) || (0, _multipleOf.ErrorMultipleOf)(stack, context, schemaPath, instancePath, schema, value)))) &
  +(!Schema.IsRef(schema) || (0, _ref.ErrorRef)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsRecursiveRef(schema) || (0, _recursiveRef.ErrorRecursiveRef)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsDynamicRef(schema) || (0, _dynamicRef.ErrorDynamicRef)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsGuard(schema) || (0, _guard.ErrorGuard)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsConst(schema) || (0, _const.ErrorConst)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsEnum(schema) || (0, _enum.ErrorEnum)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsIf(schema) || (0, _if.ErrorIf)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsNot(schema) || (0, _not.ErrorNot)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsAllOf(schema) || (0, _allOf.ErrorAllOf)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsAnyOf(schema) || (0, _anyOf.ErrorAnyOf)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsOneOf(schema) || (0, _oneOf.ErrorOneOf)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsUnevaluatedItems(schema) || !_index2.Guard.IsArray(value) || (0, _unevaluatedItems.ErrorUnevaluatedItems)(stack, context, schemaPath, instancePath, schema, value)) &
  +(!Schema.IsUnevaluatedProperties(schema) || !_index2.Guard.IsObject(value) || (0, _unevaluatedProperties.ErrorUnevaluatedProperties)(stack, context, schemaPath, instancePath, schema, value))) && (
  !Schema.IsRefine(schema) || (0, _refine.ErrorRefine)(stack, context, schemaPath, instancePath, schema, value));
  stack.Pop(schema);
  return result;
} /* v9-f4b23435dc9ae93c */
