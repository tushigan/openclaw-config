"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildMaxLength = BuildMaxLength;exports.CheckMaxLength = CheckMaxLength;exports.ErrorMaxLength = ErrorMaxLength;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildMaxLength(_stack, _context, schema, value) {
  return _index.EmitGuard.IsMaxLength(value, _index.EmitGuard.Constant(schema.maxLength));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckMaxLength(_stack, _context, schema, value) {
  return _index.Guard.IsMaxLength(value, schema.maxLength);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorMaxLength(stack, context, schemaPath, instancePath, schema, value) {
  return CheckMaxLength(stack, context, schema, value) || context.AddError({
    keyword: 'maxLength',
    schemaPath,
    instancePath,
    params: { limit: schema.maxLength }
  });
} /* v9-b990bb55bf49a1e6 */
