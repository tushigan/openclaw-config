"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsDynamicAnchor = IsDynamicAnchor;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid $dynamicAnchor property
 */
function IsDynamicAnchor(schema) {
  return _index.Guard.HasPropertyKey(schema, '$dynamicAnchor') &&
  _index.Guard.IsString(schema.$dynamicAnchor);
} /* v9-4416d67b297a7202 */
