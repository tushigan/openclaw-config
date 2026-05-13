"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildBooleanSchema = BuildBooleanSchema;exports.CheckBooleanSchema = CheckBooleanSchema;exports.ErrorBooleanSchema = ErrorBooleanSchema;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildBooleanSchema(_stack, _context, schema, _value) {
  return schema ? _index.EmitGuard.Constant(true) : _index.EmitGuard.Constant(false);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckBooleanSchema(_stack, _context, schema, _value) {
  return schema;
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorBooleanSchema(stack, context, schemaPath, instancePath, schema, value) {
  return CheckBooleanSchema(stack, context, schema, value) || context.AddError({
    keyword: 'boolean',
    schemaPath,
    instancePath,
    params: {}
  });
} /* v9-7f9c9ced281b5c3f */
