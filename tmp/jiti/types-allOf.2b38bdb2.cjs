"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsAllOf = IsAllOf;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid allOf property
 * @specification Json Schema 7
 */
function IsAllOf(schema) {
  return _index.Guard.HasPropertyKey(schema, 'allOf') &&
  _index.Guard.IsArray(schema.allOf) &&
  schema.allOf.every((value) => (0, _schema.IsSchema)(value));
} /* v9-31f3d71c1e8d3d7b */
