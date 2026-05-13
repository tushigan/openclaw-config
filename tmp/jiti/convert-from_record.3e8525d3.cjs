"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromRecord = FromRecord;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs");
var _from_additional = require("./from_additional.mjs"); // deno-fmt-ignore-file
function FromPatternProperties(context, type, value) {
  const entries = _index.Guard.EntriesRegExp(type.patternProperties);
  const keys = _index.Guard.Keys(value);
  for (const [regexp, schema] of entries) {
    for (const key of keys) {
      if (regexp.test(key)) {
        value[key] = (0, _from_type.FromType)(context, schema, value[key]);
      }
    }
  }
  return _index.Guard.HasPropertyKey(type, 'additionalProperties') && _index.Guard.IsObject(type.additionalProperties) ?
  (0, _from_additional.FromAdditionalProperties)(context, entries, type.additionalProperties, value) :
  value;
}
function FromRecord(context, type, value) {
  return _index.Guard.IsObjectNotArray(value) ?
  FromPatternProperties(context, type, value) :
  value;
} /* v9-de629fc5235f929a */
