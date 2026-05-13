"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsRef = IsRef;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid $ref property
 * @specification Json Schema 7
 */
function IsRef(schema) {
  return _index.Guard.HasPropertyKey(schema, '$ref') &&
  _index.Guard.IsString(schema.$ref);
} /* v9-57a46a82a74749af */
