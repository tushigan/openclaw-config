"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildMaximum = BuildMaximum;exports.CheckMaximum = CheckMaximum;exports.ErrorMaximum = ErrorMaximum;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildMaximum(_stack, _context, schema, value) {
  return _index.EmitGuard.IsLessEqualThan(value, _index.EmitGuard.Constant(schema.maximum));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckMaximum(_stack, _context, schema, value) {
  return _index.Guard.IsLessEqualThan(value, schema.maximum);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorMaximum(stack, context, schemaPath, instancePath, schema, value) {
  return CheckMaximum(stack, context, schema, value) || context.AddError({
    keyword: 'maximum',
    schemaPath,
    instancePath,
    params: { comparison: '<=', limit: schema.maximum }
  });
} /* v9-0f4cb7ac354a4bfc */
