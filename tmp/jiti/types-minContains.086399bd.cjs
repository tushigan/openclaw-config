"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsMinContains = IsMinContains;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid maxContains property
 * @specification Json Schema 2019-09
 */
function IsMinContains(schema) {
  return _index.Guard.HasPropertyKey(schema, 'minContains') &&
  _index.Guard.IsNumber(schema.minContains);
} /* v9-11b96ea8db74a963 */
