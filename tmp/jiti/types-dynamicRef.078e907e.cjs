"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsDynamicRef = IsDynamicRef;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid $dynamicRef property
 */
function IsDynamicRef(schema) {
  return _index.Guard.HasPropertyKey(schema, '$dynamicRef') &&
  _index.Guard.IsString(schema.$dynamicRef);
} /* v9-b59f7fbd0ca2fd61 */
