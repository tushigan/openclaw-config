"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildProperties = BuildProperties;exports.CheckProperties = CheckProperties;exports.ErrorProperties = ErrorProperties;
var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _index2 = require("../../guard/index.mjs");
var _schema = require("./schema.mjs");
var _exact_optional = require("./_exact_optional.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildProperties(stack, context, schema, value) {
  const required = Schema.IsRequired(schema) ? schema.required : [];
  const everyKey = _index2.Guard.Entries(schema.properties).map(([key, schema]) => {
    const notKey = _index2.EmitGuard.Not(_index2.EmitGuard.HasPropertyKey(value, _index2.EmitGuard.Constant(key)));
    const isSchema = (0, _schema.BuildSchemaPushStack)(stack, context, schema, _index2.EmitGuard.Member(value, key));
    const addKey = context.AddKey(_index2.EmitGuard.Constant(key));
    const guarded = context.UseUnevaluated() ? _index2.EmitGuard.And(isSchema, addKey) : isSchema;
    // --------------------------------------------------------------
    // Optimization
    //
    // If a key is required, we can skip the `notKey` check since this
    // condition is already enforced by Required. This optimization is
    // only valid when Required is evaluated before Properties.
    //
    // --------------------------------------------------------------
    const isProperty = required.includes(key) ? guarded : _index2.EmitGuard.Or(notKey, guarded);
    // --------------------------------------------------------------
    // ExactOptionalProperties
    //
    // By default, TypeScript allows optional properties to be assigned
    // undefined. This is a bit misleading, since 'optional' is usually
    // understood to mean 'the key may be absent', not 'the key may be
    // present with an undefined value'.
    //
    // The 'IsExactOptional' check returns false by default, matching
    // TypeScript's behavior. When exactOptionalPropertyTypes is enabled
    // in tsconfig.json, TypeBox can be configured to use the stricter 
    // semantics via System settings:
    //
    //   Settings.Set({ exactOptionalPropertyTypes: true })
    //
    // --------------------------------------------------------------
    return (0, _exact_optional.IsExactOptional)(required, key) ?
    isProperty :
    _index2.EmitGuard.Or((0, _exact_optional.InexactOptionalBuild)(value, key), isProperty);
  });
  return _index2.EmitGuard.ReduceAnd(everyKey);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckProperties(stack, context, schema, value) {
  const required = Schema.IsRequired(schema) ? schema.required : [];
  const isProperties = _index2.Guard.Every(_index2.Guard.Entries(schema.properties), 0, ([key, schema]) => {
    const isProperty = !_index2.Guard.HasPropertyKey(value, key) || (0, _schema.CheckSchemaPushStack)(stack, context, schema, value[key]) && context.AddKey(key);
    return (0, _exact_optional.IsExactOptional)(required, key) ?
    isProperty :
    (0, _exact_optional.InexactOptionalCheck)(value, key) || isProperty;
  });
  return isProperties;
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorProperties(stack, context, schemaPath, instancePath, schema, value) {
  const required = Schema.IsRequired(schema) ? schema.required : [];
  const isProperties = _index2.Guard.EveryAll(_index2.Guard.Entries(schema.properties), 0, ([key, schema]) => {
    const nextSchemaPath = `${schemaPath}/properties/${key}`;
    const nextInstancePath = `${instancePath}/${key}`;
    // Defer error generation for IsExactOptional
    const isProperty = () => !_index2.Guard.HasPropertyKey(value, key) || (0, _schema.ErrorSchemaPushStack)(stack, context, nextSchemaPath, nextInstancePath, schema, value[key]) && context.AddKey(key);
    return (0, _exact_optional.IsExactOptional)(required, key) ?
    isProperty() :
    (0, _exact_optional.InexactOptionalCheck)(value, key) || isProperty();
  });
  return isProperties;
} /* v9-6663db108903524e */
