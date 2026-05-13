"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsMultipleOf = IsMultipleOf;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid multipleOf property
 * @specification Json Schema 7
 */
function IsMultipleOf(schema) {
  return _index.Guard.HasPropertyKey(schema, 'multipleOf') && (
  _index.Guard.IsNumber(schema.multipleOf) || _index.Guard.IsBigInt(schema.multipleOf));
} /* v9-bc47ea7425e6dc5c */
