"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsPattern = IsPattern;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid pattern property
 * @specification Json Schema 7
 */
function IsPattern(schema) {
  return _index.Guard.HasPropertyKey(schema, 'pattern') && (
  _index.Guard.IsString(schema.pattern) ||
  schema.pattern instanceof RegExp);
} /* v9-78834703c7338194 */
