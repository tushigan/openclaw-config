"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromRecord = FromRecord;

var _index = require("../../type/index.mjs");
var _index2 = require("../../schema/types/index.mjs");
var _index3 = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
// deno-lint-ignore-file
function FromRecord(context, type, value) {if (!_index3.Guard.IsObject(value))
  return value;
  // PatternProperties
  const [recordKey, recordValue] = [new RegExp((0, _index.RecordPattern)(type)), (0, _index.RecordValue)(type)];
  for (const key of _index3.Guard.Keys(value)) {
    if (!(recordKey.test(key) && (0, _index2.IsDefault)(recordValue)))
    continue;
    value[key] = (0, _from_type.FromType)(context, recordValue, value[key]);
  }
  // AdditionalProperties
  if (!(0, _index2.IsAdditionalProperties)(type))
  return value;
  for (const key of _index3.Guard.Keys(value)) {
    if (recordKey.test(key))
    continue;
    value[key] = (0, _from_type.FromType)(context, type.additionalProperties, value[key]);
  }
  return value;
} /* v9-1732f6253ee52002 */
