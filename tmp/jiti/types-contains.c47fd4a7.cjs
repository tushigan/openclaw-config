"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsContains = IsContains;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid contains property
 * @specification Json Schema 7
 */
function IsContains(schema) {
  return _index.Guard.HasPropertyKey(schema, 'contains') &&
  (0, _schema.IsSchema)(schema.contains);
} /* v9-779caf5d3eb91bb2 */
