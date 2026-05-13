"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildPatternProperties = BuildPatternProperties;exports.CheckPatternProperties = CheckPatternProperties;exports.ErrorPatternProperties = ErrorPatternProperties;
var Externals = _interopRequireWildcard(require("./_externals.mjs"));
var _unique = require("./_unique.mjs");
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildPatternProperties(stack, context, schema, value) {
  return _index.EmitGuard.ReduceAnd(_index.Guard.Entries(schema.patternProperties).map(([pattern, schema]) => {
    const [key, prop] = [(0, _unique.Unique)(), (0, _unique.Unique)()];
    const regexp = Externals.CreateVariable(new RegExp(pattern, 'u'));
    const notKey = _index.EmitGuard.Not(_index.EmitGuard.Call(_index.EmitGuard.Member(regexp, 'test'), [key]));
    const isSchema = (0, _schema.BuildSchemaPushStack)(stack, context, schema, prop);
    const addKey = context.AddKey(key);
    const guarded = context.UseUnevaluated() ? _index.EmitGuard.Or(notKey, _index.EmitGuard.And(isSchema, addKey)) : _index.EmitGuard.Or(notKey, isSchema);
    return _index.EmitGuard.Every(_index.EmitGuard.Entries(value), _index.EmitGuard.Constant(0), [`[${key}, ${prop}]`, '_'], guarded);
  }));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckPatternProperties(stack, context, schema, value) {
  return _index.Guard.Every(_index.Guard.Entries(schema.patternProperties), 0, ([pattern, schema]) => {
    const regexp = new RegExp(pattern, 'u');
    return _index.Guard.Every(_index.Guard.Entries(value), 0, ([key, prop]) => {
      return !regexp.test(key) || (0, _schema.CheckSchemaPushStack)(stack, context, schema, prop) && context.AddKey(key);
    });
  });
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorPatternProperties(stack, context, schemaPath, instancePath, schema, value) {
  return _index.Guard.EveryAll(_index.Guard.Entries(schema.patternProperties), 0, ([pattern, schema]) => {
    const nextSchemaPath = `${schemaPath}/patternProperties/${pattern}`;
    const regexp = new RegExp(pattern, 'u');
    return _index.Guard.EveryAll(_index.Guard.Entries(value), 0, ([key, value]) => {
      const nextInstancePath = `${instancePath}/${key}`;
      const notKey = !regexp.test(key);
      return notKey || (0, _schema.ErrorSchemaPushStack)(stack, context, nextSchemaPath, nextInstancePath, schema, value) && context.AddKey(key);
    });
  });
} /* v9-043c3f7fec01c60d */
