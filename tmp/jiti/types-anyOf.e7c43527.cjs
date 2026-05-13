"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsAnyOf = IsAnyOf;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid anyOf property
 * @specification Json Schema 7
 */
function IsAnyOf(schema) {
  return _index.Guard.HasPropertyKey(schema, 'anyOf') &&
  _index.Guard.IsArray(schema.anyOf) &&
  schema.anyOf.every((value) => (0, _schema.IsSchema)(value));
} /* v9-6d3db47326b77083 */
