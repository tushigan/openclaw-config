"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildItems = BuildItems;exports.CheckItems = CheckItems;exports.ErrorItems = ErrorItems;
var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _index2 = require("../../guard/index.mjs");
var _schema = require("./schema.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// ItemsSized
// ------------------------------------------------------------------
function BuildItemsSized(stack, context, schema, value) {
  return _index2.EmitGuard.ReduceAnd(schema.items.map((schema, index) => {
    const isLength = _index2.EmitGuard.IsLessEqualThan(_index2.EmitGuard.Member(value, 'length'), _index2.EmitGuard.Constant(index));
    const isSchema = (0, _schema.BuildSchemaPushStack)(stack, context, schema, `${value}[${index}]`);
    const addIndex = context.AddIndex(_index2.EmitGuard.Constant(index));
    const guarded = context.UseUnevaluated() ? _index2.EmitGuard.And(isSchema, addIndex) : isSchema;
    return _index2.EmitGuard.Or(isLength, guarded);
  }));
}
function CheckItemsSized(stack, context, schema, value) {
  return _index2.Guard.Every(schema.items, 0, (schema, index) => {
    return _index2.Guard.IsLessEqualThan(value.length, index) ||
    (0, _schema.CheckSchemaPushStack)(stack, context, schema, value[index]) && context.AddIndex(index);
  });
}
function ErrorItemsSized(stack, context, schemaPath, instancePath, schema, value) {
  return _index2.Guard.EveryAll(schema.items, 0, (schema, index) => {
    const nextSchemaPath = `${schemaPath}/items/${index}`;
    const nextInstancePath = `${instancePath}/${index}`;
    return _index2.Guard.IsLessEqualThan(value.length, index) ||
    (0, _schema.ErrorSchemaPushStack)(stack, context, nextSchemaPath, nextInstancePath, schema, value[index]) && context.AddIndex(index);
  });
}
// ------------------------------------------------------------------
// ItemsUnsized
// ------------------------------------------------------------------
function BuildItemsUnsized(stack, context, schema, value) {
  const offset = Schema.IsPrefixItems(schema) ? schema.prefixItems.length : 0;
  const isSchema = (0, _schema.BuildSchemaPushStack)(stack, context, schema.items, 'element');
  const addIndex = context.AddIndex('index');
  const guarded = context.UseUnevaluated() ? _index2.EmitGuard.And(isSchema, addIndex) : isSchema;
  return _index2.EmitGuard.Every(value, _index2.EmitGuard.Constant(offset), ['element', 'index'], guarded);
}
function CheckItemsUnsized(stack, context, schema, value) {
  const offset = Schema.IsPrefixItems(schema) ? schema.prefixItems.length : 0;
  return _index2.Guard.Every(value, offset, (element, index) => {
    return (0, _schema.CheckSchemaPushStack)(stack, context, schema.items, element) &&
    context.AddIndex(index);
  });
}
function ErrorItemsUnsized(stack, context, schemaPath, instancePath, schema, value) {
  const offset = Schema.IsPrefixItems(schema) ? schema.prefixItems.length : 0;
  return _index2.Guard.EveryAll(value, offset, (element, index) => {
    const nextSchemaPath = `${schemaPath}/items`;
    const nextInstancePath = `${instancePath}/${index}`;
    return (0, _schema.ErrorSchemaPushStack)(stack, context, nextSchemaPath, nextInstancePath, schema.items, element) &&
    context.AddIndex(index);
  });
}
// ------------------------------------------------------------------
// Items
// ------------------------------------------------------------------
function BuildItems(stack, context, schema, value) {
  return Schema.IsItemsSized(schema) ? BuildItemsSized(stack, context, schema, value) : BuildItemsUnsized(stack, context, schema, value);
}
function CheckItems(stack, context, schema, value) {
  return Schema.IsItemsSized(schema) ? CheckItemsSized(stack, context, schema, value) : CheckItemsUnsized(stack, context, schema, value);
}
function ErrorItems(stack, context, schemaPath, instancePath, schema, value) {
  return Schema.IsItemsSized(schema) ? ErrorItemsSized(stack, context, schemaPath, instancePath, schema, value) : ErrorItemsUnsized(stack, context, schemaPath, instancePath, schema, value);
} /* v9-c2eb2e166f916ca8 */
