"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsFormat = IsFormat;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid format property
 * @specification Json Schema 7
 */
function IsFormat(schema) {
  return _index.Guard.HasPropertyKey(schema, 'format') &&
  _index.Guard.IsString(schema.format);
} /* v9-bdea284fa411394e */
