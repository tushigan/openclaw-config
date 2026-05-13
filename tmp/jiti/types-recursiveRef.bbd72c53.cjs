"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsRecursiveRef = IsRecursiveRef;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid $recursiveRef property
 */
function IsRecursiveRef(schema) {
  return _index.Guard.HasPropertyKey(schema, '$recursiveRef') &&
  _index.Guard.IsString(schema.$recursiveRef);
} /* v9-be23ed0b23a4cf8d */
