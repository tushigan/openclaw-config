"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildMaxItems = BuildMaxItems;exports.CheckMaxItems = CheckMaxItems;exports.ErrorMaxItems = ErrorMaxItems;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildMaxItems(_stack, _context, schema, value) {
  return _index.EmitGuard.IsLessEqualThan(_index.EmitGuard.Member(value, 'length'), _index.EmitGuard.Constant(schema.maxItems));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckMaxItems(_stack, _context, schema, value) {
  return _index.Guard.IsLessEqualThan(value.length, schema.maxItems);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorMaxItems(stack, context, schemaPath, instancePath, schema, value) {
  return CheckMaxItems(stack, context, schema, value) || context.AddError({
    keyword: 'maxItems',
    schemaPath,
    instancePath,
    params: { limit: schema.maxItems }
  });
} /* v9-240856b1b4a95c54 */
