"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsDependentRequired = IsDependentRequired;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid dependentRequired property
 * @specification Json Schema 2019-09
 */
function IsDependentRequired(schema) {
  return _index.Guard.HasPropertyKey(schema, 'dependentRequired') &&
  _index.Guard.IsObject(schema.dependentRequired) &&
  Object.values(schema.dependentRequired).every((value) => _index.Guard.IsArray(value) &&
  value.every((value) => _index.Guard.IsString(value)));
} /* v9-9e47d8612c6133b8 */
