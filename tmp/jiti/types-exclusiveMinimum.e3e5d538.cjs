"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsExclusiveMinimum = IsExclusiveMinimum;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid exclusiveMinimum property
 * @specification Json Schema 7
 */
function IsExclusiveMinimum(schema) {
  return _index.Guard.HasPropertyKey(schema, 'exclusiveMinimum') && (
  _index.Guard.IsNumber(schema.exclusiveMinimum) || _index.Guard.IsBigInt(schema.exclusiveMinimum));
} /* v9-ae5c910405b63379 */
