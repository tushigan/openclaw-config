"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildRequired = BuildRequired;exports.CheckRequired = CheckRequired;exports.ErrorRequired = ErrorRequired;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildRequired(_stack, _context, schema, value) {
  return _index.EmitGuard.ReduceAnd(schema.required.map((key) => _index.EmitGuard.HasPropertyKey(value, _index.EmitGuard.Constant(key))));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckRequired(_stack, _context, schema, value) {
  return _index.Guard.Every(schema.required, 0, (key) => _index.Guard.HasPropertyKey(value, key));
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorRequired(_stack, context, schemaPath, instancePath, schema, value) {
  const requiredProperties = [];
  const isRequired = _index.Guard.EveryAll(schema.required, 0, (key) => {
    const hasKey = _index.Guard.HasPropertyKey(value, key);
    if (!hasKey)
    requiredProperties.push(key);
    return hasKey;
  });
  return isRequired || context.AddError({
    keyword: 'required',
    schemaPath,
    instancePath,
    params: { requiredProperties }
  });
} /* v9-a506567edca1baf9 */
