"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsMaxProperties = IsMaxProperties;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid maxProperties property
 * @specification Json Schema 7
 */
function IsMaxProperties(schema) {
  return _index.Guard.HasPropertyKey(schema, 'maxProperties') &&
  _index.Guard.IsNumber(schema.maxProperties);
} /* v9-91727021883d34af */
