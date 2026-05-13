"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildAdditionalProperties = BuildAdditionalProperties;exports.BuildAdditionalPropertiesFast = BuildAdditionalPropertiesFast;exports.BuildAdditionalPropertiesStandard = BuildAdditionalPropertiesStandard;exports.CanAdditionalPropertiesFast = CanAdditionalPropertiesFast;exports.CheckAdditionalProperties = CheckAdditionalProperties;exports.ErrorAdditionalProperties = ErrorAdditionalProperties;
var S = _interopRequireWildcard(require("../types/index.mjs"));
var V = _interopRequireWildcard(require("./_externals.mjs"));
var _unique = require("./_unique.mjs");
var _context2 = require("./_context.mjs");
var _index3 = require("../../guard/index.mjs");
var _schema = require("./schema.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Common: GetPropertiesPattern
//
// Constructs a regular expression that matches all property keys
// and pattern properties defined in a schema. This approach unifies
// handling of both property types, avoiding separate logic paths.
//
// If no keys or patterns are present, it returns a pattern that
// matches nothing: '(?!)'.
//
// ------------------------------------------------------------------
function GetPropertyKeyAsPattern(key) {
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return `^${escaped}$`;
}
function GetPropertiesPattern(schema) {
  const patterns = [];
  if (S.IsPatternProperties(schema))
  patterns.push(..._index3.Guard.Keys(schema.patternProperties));
  if (S.IsProperties(schema))
  patterns.push(..._index3.Guard.Keys(schema.properties).map(GetPropertyKeyAsPattern));
  return _index3.Guard.IsEqual(patterns.length, 0) ? '(?!)' : `(${patterns.join('|')})`;
}
// ------------------------------------------------------------------
// BuildAdditionalPropertiesFast
//
// Optimized logic for schemas with `additionalProperties: false`.
//
// This fast-path applies only when:
// - `additionalProperties` is explicitly set to false,
// - the schema uses only `properties` (no `patternProperties`),
// - and all defined properties are required (i.e., no optional keys).
//
// This constraint is common when enforcing strict object shapes
// with only known, fixed keys. When all these conditions are met,
// we can generate a simplified and efficient runtime check.
//
// ------------------------------------------------------------------
function CanAdditionalPropertiesFast(_context, schema, _value) {
  return S.IsRequired(schema) &&
  S.IsProperties(schema) &&
  !S.IsPatternProperties(schema) &&
  _index3.Guard.IsEqual(schema.additionalProperties, false) &&
  _index3.Guard.IsEqual(_index3.Guard.Keys(schema.properties).length, schema.required.length);
}
function BuildAdditionalPropertiesFast(_context, schema, value) {
  return _index3.EmitGuard.IsEqual(_index3.EmitGuard.Member(_index3.EmitGuard.Call(_index3.EmitGuard.Member('Object', 'getOwnPropertyNames'), [value]), 'length'), _index3.EmitGuard.Constant(schema.required.length));
}
// ------------------------------------------------------------------
// BuildAdditionalPropertiesStandard
// ------------------------------------------------------------------
function BuildAdditionalPropertiesStandard(stack, context, schema, value) {
  const [key, _index] = [(0, _unique.Unique)(), (0, _unique.Unique)()];
  const regexp = V.CreateVariable(new RegExp(GetPropertiesPattern(schema)));
  const isSchema = (0, _schema.BuildSchemaPushStack)(stack, context, schema.additionalProperties, `${value}[${key}]`);
  const isKey = _index3.EmitGuard.Call(_index3.EmitGuard.Member(regexp, 'test'), [key]);
  const addKey = context.AddKey(key);
  const guarded = context.UseUnevaluated() ? _index3.EmitGuard.Or(isKey, _index3.EmitGuard.And(isSchema, addKey)) : _index3.EmitGuard.Or(isKey, isSchema);
  const result = _index3.EmitGuard.Every(_index3.EmitGuard.Keys(value), _index3.EmitGuard.Constant(0), [key, _index], guarded);
  return result;
}
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildAdditionalProperties(stack, context, schema, value) {
  return CanAdditionalPropertiesFast(context, schema, value) ?
  BuildAdditionalPropertiesFast(context, schema, value) :
  BuildAdditionalPropertiesStandard(stack, context, schema, value);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckAdditionalProperties(stack, context, schema, value) {
  const regexp = new RegExp(GetPropertiesPattern(schema));
  const isAdditionalProperties = _index3.Guard.Every(_index3.Guard.Keys(value), 0, (key, _index) => {
    return regexp.test(key) ||
    (0, _schema.CheckSchemaPushStack)(stack, context, schema.additionalProperties, value[key]) && context.AddKey(key);
  });
  return isAdditionalProperties;
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorAdditionalProperties(stack, context, schemaPath, instancePath, schema, value) {
  const regexp = new RegExp(GetPropertiesPattern(schema));
  const additionalProperties = [];
  const isAdditionalProperties = _index3.Guard.EveryAll(_index3.Guard.Keys(value), 0, (key, _index) => {
    const nextSchemaPath = `${schemaPath}/additionalProperties`;
    const nextInstancePath = `${instancePath}/${key}`;
    const nextContext = new _context2.AccumulatedErrorContext();
    const isAdditionalProperty = regexp.test(key) ||
    (0, _schema.ErrorSchemaPushStack)(stack, nextContext, nextSchemaPath, nextInstancePath, schema.additionalProperties, value[key]) && context.AddKey(key);
    if (!isAdditionalProperty)
    additionalProperties.push(key);
    return isAdditionalProperty;
  });
  return isAdditionalProperties || context.AddError({
    keyword: 'additionalProperties',
    schemaPath,
    instancePath: instancePath,
    params: { additionalProperties }
  });
} /* v9-9bbf1ed27a33534a */
