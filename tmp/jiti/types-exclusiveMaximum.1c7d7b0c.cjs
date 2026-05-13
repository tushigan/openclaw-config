"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsExclusiveMaximum = IsExclusiveMaximum;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid exclusiveMaximum property
 * @specification Json Schema 7
 */
function IsExclusiveMaximum(schema) {
  return _index.Guard.HasPropertyKey(schema, 'exclusiveMaximum') && (
  _index.Guard.IsNumber(schema.exclusiveMaximum) || _index.Guard.IsBigInt(schema.exclusiveMaximum));
} /* v9-8867ebb44929fc8d */
