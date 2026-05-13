"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsElse = IsElse;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid else property
 * @specification Json Schema 7
 */
function IsElse(schema) {
  return _index.Guard.HasPropertyKey(schema, 'else') &&
  (0, _schema.IsSchema)(schema.else);
} /* v9-ea5f4befca7d419d */
