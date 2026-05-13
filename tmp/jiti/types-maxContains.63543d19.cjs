"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsMaxContains = IsMaxContains;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid maxContains property
 * @specification Json Schema 2019-09
 */
function IsMaxContains(schema) {
  return _index.Guard.HasPropertyKey(schema, 'maxContains') &&
  _index.Guard.IsNumber(schema.maxContains);
} /* v9-945e98c54b7d7259 */
