"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildMultipleOf = BuildMultipleOf;exports.CheckMultipleOf = CheckMultipleOf;exports.ErrorMultipleOf = ErrorMultipleOf;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildMultipleOf(_stack, _context, schema, value) {
  return _index.EmitGuard.MultipleOf(value, _index.EmitGuard.Constant(schema.multipleOf));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckMultipleOf(_stack, _context, schema, value) {
  return _index.Guard.IsMultipleOf(value, schema.multipleOf);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorMultipleOf(stack, context, schemaPath, instancePath, schema, value) {
  return CheckMultipleOf(stack, context, schema, value) || context.AddError({
    keyword: 'multipleOf',
    schemaPath,
    instancePath,
    params: { multipleOf: schema.multipleOf }
  });
} /* v9-27f51abeba9cb15e */
