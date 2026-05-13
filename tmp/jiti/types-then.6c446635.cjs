"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsThen = IsThen;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid then property
 * @specification Json Schema 7
 */
function IsThen(schema) {
  return _index.Guard.HasPropertyKey(schema, 'then') &&
  (0, _schema.IsSchema)(schema.then);
} /* v9-1ce69025529d1853 */
