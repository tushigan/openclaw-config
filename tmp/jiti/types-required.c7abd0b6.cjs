"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsRequired = IsRequired;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid required property
 * @specification Json Schema 7
 */
function IsRequired(schema) {
  return _index.Guard.HasPropertyKey(schema, 'required') &&
  _index.Guard.IsArray(schema.required) &&
  schema.required.every((value) => _index.Guard.IsString(value));
} /* v9-6b0a7e2ca3a3968a */
