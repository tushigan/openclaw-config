"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildPropertyNames = BuildPropertyNames;exports.CheckPropertyNames = CheckPropertyNames;exports.ErrorPropertyNames = ErrorPropertyNames;
var _unique = require("./_unique.mjs");
var _context = require("./_context.mjs");
var _index2 = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildPropertyNames(stack, context, schema, value) {
  const [key, _index] = [(0, _unique.Unique)(), (0, _unique.Unique)()];
  return _index2.EmitGuard.Every(_index2.EmitGuard.Keys(value), _index2.EmitGuard.Constant(0), [key, _index], (0, _schema.BuildSchema)(stack, context, schema.propertyNames, key));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckPropertyNames(stack, context, schema, value) {
  return _index2.Guard.Every(_index2.Guard.Keys(value), 0, (key, _index) => (0, _schema.CheckSchema)(stack, context, schema.propertyNames, key));
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorPropertyNames(stack, context, schemaPath, instancePath, schema, value) {
  const propertyNames = [];
  const isPropertyNames = _index2.Guard.EveryAll(_index2.Guard.Keys(value), 0, (key, _index) => {
    const nextInstancePath = `${instancePath}/${key}`;
    const nextSchemaPath = `${schemaPath}/propertyNames`;
    const nextContext = new _context.AccumulatedErrorContext();
    const isPropertyName = (0, _schema.ErrorSchema)(stack, nextContext, nextSchemaPath, nextInstancePath, schema.propertyNames, key);
    if (!isPropertyName)
    propertyNames.push(key);
    return isPropertyName;
  });
  return isPropertyNames || context.AddError({
    keyword: 'propertyNames',
    schemaPath,
    instancePath,
    params: { propertyNames }
  });
} /* v9-94280c7487360488 */
