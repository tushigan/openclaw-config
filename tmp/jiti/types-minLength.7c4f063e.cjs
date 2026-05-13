"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsMinLength = IsMinLength;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid minLength property
 * @specification Json Schema 7
 */
function IsMinLength(schema) {
  return _index.Guard.HasPropertyKey(schema, 'minLength') &&
  _index.Guard.IsNumber(schema.minLength);
} /* v9-e4eab55fc9f63b6f */
