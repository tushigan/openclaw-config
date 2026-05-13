"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsType = IsType;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid type property
 * @specification Json Schema 7
 */
function IsType(schema) {
  return _index.Guard.HasPropertyKey(schema, 'type') && (
  _index.Guard.IsString(schema.type) ||
  _index.Guard.IsArray(schema.type) &&
  schema.type.every((value) => _index.Guard.IsString(value)));
} /* v9-bfb6ed061f71cb66 */
