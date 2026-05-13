"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromRecord = FromRecord;
var _index = require("../../type/index.mjs");
var _index2 = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs");
var _index3 = require("../check/index.mjs");
var _additional = require("./additional.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// FromRecord
// ------------------------------------------------------------------
function FromRecord(context, type, value) {
  if (!_index2.Guard.IsObject(value))
  return value;
  const additionalProperties = (0, _additional.GetAdditionalProperties)(type);
  const [recordPattern, recordValue] = [new RegExp((0, _index.RecordPattern)(type)), (0, _index.RecordValue)(type)];
  for (const key of _index2.Guard.Keys(value)) {
    if (recordPattern.test(key)) {
      value[key] = (0, _from_type.FromType)(context, recordValue, value[key]);
      continue;
    }
    const unknownCheck =
    // 1. additionalProperties: true
    _index2.Guard.IsBoolean(additionalProperties) && _index2.Guard.IsEqual(additionalProperties, true)
    // 2. additionalProperties: TSchema
    || (0, _index.IsSchema)(additionalProperties) && (0, _index3.Check)(context, additionalProperties, value[key]);
    if (unknownCheck) {
      value[key] = (0, _from_type.FromType)(context, additionalProperties, value[key]);
      continue;
    }
    delete value[key];
  }
  return value;
} /* v9-9697850f0ef7fbe8 */
