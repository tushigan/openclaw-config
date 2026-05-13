"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsUniqueItems = IsUniqueItems;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid uniqueItems property
 * @specification Json Schema 7
 */
function IsUniqueItems(schema) {
  return _index.Guard.HasPropertyKey(schema, 'uniqueItems') &&
  _index.Guard.IsBoolean(schema.uniqueItems);
} /* v9-9d0cb0aff21531e6 */
