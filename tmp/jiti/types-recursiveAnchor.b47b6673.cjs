"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsRecursiveAnchor = IsRecursiveAnchor;exports.IsRecursiveAnchorTrue = IsRecursiveAnchorTrue;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid $recursiveAnchor property
 */
function IsRecursiveAnchor(schema) {
  return _index.Guard.HasPropertyKey(schema, '$recursiveAnchor') &&
  _index.Guard.IsBoolean(schema.$recursiveAnchor);
}
/**
 * Returns true if the schema contains a valid $recursiveAnchor property that is true
 */
function IsRecursiveAnchorTrue(schema) {
  return IsRecursiveAnchor(schema) &&
  _index.Guard.IsEqual(schema.$recursiveAnchor, true);
} /* v9-e28f3bbffe5c4b34 */
