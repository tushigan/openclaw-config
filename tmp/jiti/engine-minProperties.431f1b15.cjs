"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildMinProperties = BuildMinProperties;exports.CheckMinProperties = CheckMinProperties;exports.ErrorMinProperties = ErrorMinProperties;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildMinProperties(_stack, _context, schema, value) {
  return _index.EmitGuard.IsGreaterEqualThan(_index.EmitGuard.Member(_index.EmitGuard.Keys(value), 'length'), _index.EmitGuard.Constant(schema.minProperties));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckMinProperties(_stack, _context, schema, value) {
  return _index.Guard.IsGreaterEqualThan(_index.Guard.Keys(value).length, schema.minProperties);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorMinProperties(stack, context, schemaPath, instancePath, schema, value) {
  return CheckMinProperties(stack, context, schema, value) || context.AddError({
    keyword: 'minProperties',
    schemaPath,
    instancePath,
    params: { limit: schema.minProperties }
  });
} /* v9-8c5db5bda986fc6d */
