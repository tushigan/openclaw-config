"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsContentEncoding = IsContentEncoding;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid contentEncoding property
 * @specification Json Schema 7
 */
function IsContentEncoding(schema) {
  return _index.Guard.HasPropertyKey(schema, 'contentEncoding') &&
  _index.Guard.IsString(schema.contentEncoding);
} /* v9-674b38b9d7617035 */
