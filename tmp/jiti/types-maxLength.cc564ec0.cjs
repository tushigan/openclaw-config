"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsMaxLength = IsMaxLength;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid maxLength property
 * @specification Json Schema 7
 */
function IsMaxLength(schema) {
  return _index.Guard.HasPropertyKey(schema, 'maxLength') &&
  _index.Guard.IsNumber(schema.maxLength);
} /* v9-154793a99a8f0200 */
