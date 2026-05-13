"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildExclusiveMaximum = BuildExclusiveMaximum;exports.CheckExclusiveMaximum = CheckExclusiveMaximum;exports.ErrorExclusiveMaximum = ErrorExclusiveMaximum;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildExclusiveMaximum(_stack, _context, schema, value) {
  return _index.EmitGuard.IsLessThan(value, _index.EmitGuard.Constant(schema.exclusiveMaximum));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckExclusiveMaximum(_stack, _context, schema, value) {
  return _index.Guard.IsLessThan(value, schema.exclusiveMaximum);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorExclusiveMaximum(stack, context, schemaPath, instancePath, schema, value) {
  return CheckExclusiveMaximum(stack, context, schema, value) || context.AddError({
    keyword: 'exclusiveMaximum',
    schemaPath,
    instancePath,
    params: { comparison: '<', limit: schema.exclusiveMaximum }
  });
} /* v9-8b698109e2eb6049 */
