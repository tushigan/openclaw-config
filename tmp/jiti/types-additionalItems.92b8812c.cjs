"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsAdditionalItems = IsAdditionalItems;
var _index = require("../../guard/index.mjs");
var _schema = require("../types/schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid additionalItems property
 * @specification Json Schema 7
 */
function IsAdditionalItems(schema) {
  return _index.Guard.HasPropertyKey(schema, 'additionalItems') &&
  (0, _schema.IsSchema)(schema.additionalItems);
} /* v9-20e10b91443265ee */
