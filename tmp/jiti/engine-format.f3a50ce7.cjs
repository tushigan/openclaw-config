"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildFormat = BuildFormat;exports.CheckFormat = CheckFormat;exports.ErrorFormat = ErrorFormat;
var _index = require("../../format/index.mjs");
var _index2 = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildFormat(_stack, _context, schema, value) {
  return _index2.EmitGuard.Call(_index2.EmitGuard.Member('Format', 'Test'), [_index2.EmitGuard.Constant(schema.format), value]);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckFormat(_stack, _context, schema, value) {
  return _index.Format.Test(schema.format, value);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorFormat(stack, context, schemaPath, instancePath, schema, value) {
  return CheckFormat(stack, context, schema, value) || context.AddError({
    keyword: 'format',
    schemaPath,
    instancePath,
    params: { format: schema.format }
  });
} /* v9-ae5e4cba3f83f707 */
