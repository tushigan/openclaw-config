"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildMaxProperties = BuildMaxProperties;exports.CheckMaxProperties = CheckMaxProperties;exports.ErrorMaxProperties = ErrorMaxProperties;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildMaxProperties(_stack, _context, schema, value) {
  return _index.EmitGuard.IsLessEqualThan(_index.EmitGuard.Member(_index.EmitGuard.Keys(value), 'length'), _index.EmitGuard.Constant(schema.maxProperties));
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckMaxProperties(_stack, _context, schema, value) {
  return _index.Guard.IsLessEqualThan(_index.Guard.Keys(value).length, schema.maxProperties);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function ErrorMaxProperties(stack, context, schemaPath, instancePath, schema, value) {
  return CheckMaxProperties(stack, context, schema, value) || context.AddError({
    keyword: 'maxProperties',
    schemaPath,
    instancePath,
    params: { limit: schema.maxProperties }
  });
} /* v9-3d1492ccae938be7 */
