"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildAdditionalItems = BuildAdditionalItems;exports.CheckAdditionalItems = CheckAdditionalItems;exports.ErrorAdditionalItems = ErrorAdditionalItems;
var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _unique = require("./_unique.mjs");
var _index2 = require("../../guard/index.mjs");
var _schema = require("./schema.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Valid
// ------------------------------------------------------------------
function IsValid(schema) {
  return Schema.IsItems(schema) && _index2.Guard.IsArray(schema.items);
}
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildAdditionalItems(stack, context, schema, value) {
  if (!IsValid(schema))
  return _index2.EmitGuard.Constant(true);
  const [item, index] = [(0, _unique.Unique)(), (0, _unique.Unique)()];
  const isSchema = (0, _schema.BuildSchemaPushStack)(stack, context, schema.additionalItems, item);
  const isLength = _index2.EmitGuard.IsLessThan(index, _index2.EmitGuard.Constant(schema.items.length));
  const addIndex = context.AddIndex(index);
  const guarded = context.UseUnevaluated() ? _index2.EmitGuard.Or(isLength, _index2.EmitGuard.And(isSchema, addIndex)) : _index2.EmitGuard.Or(isLength, isSchema);
  return _index2.EmitGuard.Call(_index2.EmitGuard.Member(value, 'every'), [_index2.EmitGuard.ArrowFunction([item, index], guarded)]);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckAdditionalItems(stack, context, schema, value) {
  if (!IsValid(schema))
  return true;
  const isAdditionalItems = value.every((item, index) => {
    return _index2.Guard.IsLessThan(index, schema.items.length) ||
    (0, _schema.CheckSchemaPushStack)(stack, context, schema.additionalItems, item) && context.AddIndex(index);
  });
  return isAdditionalItems;
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorAdditionalItems(stack, context, schemaPath, instancePath, schema, value) {
  if (!IsValid(schema))
  return true;
  const isAdditionalItems = value.every((item, index) => {
    const nextSchemaPath = `${schemaPath}/additionalItems`;
    const nextInstancePath = `${instancePath}/${index}`;
    return _index2.Guard.IsLessThan(index, schema.items.length) ||
    (0, _schema.ErrorSchemaPushStack)(stack, context, nextSchemaPath, nextInstancePath, schema.additionalItems, item) && context.AddIndex(index);
  });
  return isAdditionalItems;
} /* v9-e255ba0d1add7c11 */
