"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsId = IsId;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid $id property
 * @specification Json Schema 7
 */
function IsId(schema) {
  return _index.Guard.HasPropertyKey(schema, '$id') &&
  _index.Guard.IsString(schema.$id);
} /* v9-00d7cd339f97aa3c */
