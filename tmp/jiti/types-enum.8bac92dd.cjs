"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsEnum = IsEnum;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid enum property
 * @specification Json Schema 7
 */
function IsEnum(schema) {
  return _index.Guard.HasPropertyKey(schema, 'enum') &&
  _index.Guard.IsArray(schema.enum);
} /* v9-27e9e6b1397f7670 */
