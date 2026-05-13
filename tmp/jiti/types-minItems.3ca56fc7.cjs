"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsMinItems = IsMinItems;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid minItems property
 * @specification Json Schema 7
 */
function IsMinItems(schema) {
  return _index.Guard.HasPropertyKey(schema, 'minItems') &&
  _index.Guard.IsNumber(schema.minItems);
} /* v9-0c2ef82c74f894e9 */
