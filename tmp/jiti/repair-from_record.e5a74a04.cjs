"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromRecord = FromRecord;
var _index = require("../../schema/types/index.mjs");
var _index2 = require("../../type/index.mjs");
var _index3 = require("../../guard/index.mjs");
var _index4 = require("../create/index.mjs");
var _index5 = require("../check/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromRecord(context, type, value) {
  if ((0, _index5.Check)(context, type, value))
  return value;
  if (_index3.Guard.IsNull(value) || !_index3.Guard.IsObject(value) || _index3.Guard.IsArray(value))
  return (0, _index4.Create)(context, type);
  const recordKey = new RegExp((0, _index2.RecordPattern)(type));
  const recordValue = (0, _index2.RecordValue)(type);
  const evaluatedKeys = new Set();
  // PatternProperties
  const result = {};
  for (const [key, value_] of _index3.Guard.Entries(value)) {
    if (!recordKey.test(key))
    continue;
    result[key] = (0, _from_type.FromType)(context, recordValue, value_);
    evaluatedKeys.add(key);
  }
  // AdditionalProperties
  if ((0, _index.IsAdditionalProperties)(type)) {
    for (const key of _index3.Guard.Keys(value)) {
      if (evaluatedKeys.has(key))
      continue;
      result[key] = (0, _from_type.FromType)(context, type.additionalProperties, value[key]);
    }
  }
  return result;
} /* v9-95d8db6b6e0446c5 */
