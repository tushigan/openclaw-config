"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsMinimum = IsMinimum;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid minimum property
 * @specification Json Schema 7
 */
function IsMinimum(schema) {
  return _index.Guard.HasPropertyKey(schema, 'minimum') && (
  _index.Guard.IsNumber(schema.minimum) || _index.Guard.IsBigInt(schema.minimum));
} /* v9-7d67d6f281161513 */
