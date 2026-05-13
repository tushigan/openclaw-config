"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsAnchor = IsAnchor;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid $anchor property
 */
function IsAnchor(schema) {
  return _index.Guard.HasPropertyKey(schema, '$anchor') &&
  _index.Guard.IsString(schema.$anchor);
} /* v9-ea6bcb0775cfabaf */
