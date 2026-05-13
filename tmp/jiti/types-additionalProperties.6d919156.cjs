"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsAdditionalProperties = IsAdditionalProperties;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid additionalProperties property
 * @specification Json Schema 7
 */
function IsAdditionalProperties(schema) {
  return _index.Guard.HasPropertyKey(schema, 'additionalProperties') &&
  (0, _schema.IsSchema)(schema.additionalProperties);
} /* v9-8a1cefa68b0809c6 */
