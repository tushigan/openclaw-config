"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromAdditionalProperties = FromAdditionalProperties;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
/**
 * Used by Object and Record Types. The entries are derived from the known
 * properties obtained from 'properties' and 'patternProperties' respectively.
 */
function FromAdditionalProperties(context, entries, additionalProperties, value) {
  const keys = _index.Guard.Keys(value);
  for (const [regexp, _] of entries) {
    for (const key of keys) {
      if (!regexp.test(key)) {
        value[key] = (0, _from_type.FromType)(context, additionalProperties, value[key]);
      }
    }
  }
  return value;
} /* v9-38d50663cf6ce757 */
