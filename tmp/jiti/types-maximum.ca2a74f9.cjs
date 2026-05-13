"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsMaximum = IsMaximum;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid maximum property
 * @specification Json Schema 7
 */
function IsMaximum(schema) {
  return _index.Guard.HasPropertyKey(schema, 'maximum') && (
  _index.Guard.IsNumber(schema.maximum) || _index.Guard.IsBigInt(schema.maximum));
} /* v9-5934e58be8ea8906 */
