"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsContentMediaType = IsContentMediaType;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid contentMediaType property
 * @specification Json Schema 7
 */
function IsContentMediaType(schema) {
  return _index.Guard.HasPropertyKey(schema, 'contentMediaType') &&
  _index.Guard.IsString(schema.contentMediaType);
} /* v9-f6d0b5cdfa46ac97 */
