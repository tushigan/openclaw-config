"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildMinimum = BuildMinimum;exports.CheckMinimum = CheckMinimum;exports.ErrorMinimum = ErrorMinimum;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildMinimum(_stack, _context, schema, value) {
  return _index.EmitGuard.IsGreaterEqualThan(value, _index.EmitGuard.Constant(schema.minimum));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckMinimum(_stack, _context, schema, value) {
  return _index.Guard.IsGreaterEqualThan(value, schema.minimum);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorMinimum(stack, context, schemaPath, instancePath, schema, value) {
  return CheckMinimum(stack, context, schema, value) || context.AddError({
    keyword: 'minimum',
    schemaPath,
    instancePath,
    params: { comparison: '>=', limit: schema.minimum }
  });
} /* v9-473b9ea302cd3dde */
