"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsMinProperties = IsMinProperties;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid minProperties property
 * @specification Json Schema 7
 */
function IsMinProperties(schema) {
  return _index.Guard.HasPropertyKey(schema, 'minProperties') &&
  _index.Guard.IsNumber(schema.minProperties);
} /* v9-7d0989fb16335d49 */
