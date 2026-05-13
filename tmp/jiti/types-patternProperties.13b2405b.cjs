"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsPatternProperties = IsPatternProperties;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid patternProperties property
 * @specification Json Schema 7
 */
function IsPatternProperties(schema) {
  return _index.Guard.HasPropertyKey(schema, 'patternProperties') &&
  _index.Guard.IsObject(schema.patternProperties) &&
  Object.values(schema.patternProperties).every((value) => (0, _schema.IsSchema)(value));
} /* v9-fa71bcb0ce1d4597 */
