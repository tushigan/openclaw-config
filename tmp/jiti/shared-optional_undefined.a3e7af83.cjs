"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsOptionalUndefined = IsOptionalUndefined;
var _index = require("../../guard/index.mjs");
var _index2 = require("../../type/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// IsOptionalUndefined
//
// Indicates whether a key should be excluded from processing when it is 
// defined as optional in the schema and its corresponding value is undefined. 
// This case cannot be reliably distinguished from an omitted key, and therefore 
// introduces ambiguity between a key that is not provided and one that is 
// explicitly assigned an undefined value.
// ------------------------------------------------------------------
function IsOptionalUndefined(property, key, value) {
  return (0, _index2.IsOptional)(property) && _index.Guard.IsUndefined(value[key]);
} /* v9-2e1e858fad44310a */
