"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildExclusiveMinimum = BuildExclusiveMinimum;exports.CheckExclusiveMinimum = CheckExclusiveMinimum;exports.ErrorExclusiveMinimum = ErrorExclusiveMinimum;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildExclusiveMinimum(_stack, _context, schema, value) {
  return _index.EmitGuard.IsGreaterThan(value, _index.EmitGuard.Constant(schema.exclusiveMinimum));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckExclusiveMinimum(_stack, _context, schema, value) {
  return _index.Guard.IsGreaterThan(value, schema.exclusiveMinimum);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorExclusiveMinimum(stack, context, schemaPath, instancePath, schema, value) {
  return CheckExclusiveMinimum(stack, context, schema, value) || context.AddError({
    keyword: 'exclusiveMinimum',
    schemaPath,
    instancePath,
    params: { comparison: '>', limit: schema.exclusiveMinimum }
  });
} /* v9-22b75a1d4b152c7b */
