"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildMinLength = BuildMinLength;exports.CheckMinLength = CheckMinLength;exports.ErrorMinLength = ErrorMinLength;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildMinLength(_stack, _context, schema, value) {
  return _index.EmitGuard.IsMinLength(value, _index.EmitGuard.Constant(schema.minLength));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckMinLength(_stack, _context, schema, value) {
  return _index.Guard.IsMinLength(value, schema.minLength);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorMinLength(stack, context, schemaPath, instancePath, schema, value) {
  return CheckMinLength(stack, context, schema, value) || context.AddError({
    keyword: 'minLength',
    schemaPath,
    instancePath,
    params: { limit: schema.minLength }
  });
} /* v9-5acc3bd942be3f0d */
