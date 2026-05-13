"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsMaxItems = IsMaxItems;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid maxItems property
 * @specification Json Schema 7
 */
function IsMaxItems(schema) {
  return _index.Guard.HasPropertyKey(schema, 'maxItems') &&
  _index.Guard.IsNumber(schema.maxItems);
} /* v9-4d5f60b272b3e0cd */
