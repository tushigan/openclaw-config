"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromObject = FromObject;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs");
var _from_additional = require("./from_additional.mjs");
var _optional_undefined = require("../shared/optional_undefined.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// FromProperties
// ------------------------------------------------------------------
function FromProperties(context, type, value) {
  const entries = _index.Guard.EntriesRegExp(type.properties);
  const keys = _index.Guard.Keys(value);
  for (const [regexp, property] of entries) {
    for (const key of keys) {
      // Ignore for non-present or optional-undefined
      if (!regexp.test(key) || (0, _optional_undefined.IsOptionalUndefined)(property, key, value))
      continue;
      value[key] = (0, _from_type.FromType)(context, property, value[key]);
    }
  }
  return _index.Guard.HasPropertyKey(type, 'additionalProperties') && _index.Guard.IsObject(type.additionalProperties) ?
  (0, _from_additional.FromAdditionalProperties)(context, entries, type.additionalProperties, value) :
  value;
}
function FromObject(context, type, value) {
  return _index.Guard.IsObjectNotArray(value) ?
  FromProperties(context, type, value) :
  value;
} /* v9-fd76ce023f8f13b2 */
