"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildMinItems = BuildMinItems;exports.CheckMinItems = CheckMinItems;exports.ErrorMinItems = ErrorMinItems;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildMinItems(_stack, _context, schema, value) {
  return _index.EmitGuard.IsGreaterEqualThan(_index.EmitGuard.Member(value, 'length'), _index.EmitGuard.Constant(schema.minItems));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckMinItems(_stack, _context, schema, value) {
  return _index.Guard.IsGreaterEqualThan(value.length, schema.minItems);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorMinItems(stack, context, schemaPath, instancePath, schema, value) {
  return CheckMinItems(stack, context, schema, value) || context.AddError({
    keyword: 'minItems',
    schemaPath,
    instancePath,
    params: { limit: schema.minItems }
  });
} /* v9-e39d13197f93d792 */
