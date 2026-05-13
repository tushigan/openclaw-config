"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromObject = FromObject;
var _index = require("../../type/index.mjs");
var _index2 = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs");
var _index3 = require("../check/index.mjs");
var _additional = require("./additional.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// FromObject
// ------------------------------------------------------------------
function FromObject(context, type, value) {
  if (!_index2.Guard.IsObject(value) || _index2.Guard.IsArray(value))
  return value;
  const additionalProperties = (0, _additional.GetAdditionalProperties)(type);
  for (const key of _index2.Guard.Keys(value)) {
    if (_index2.Guard.HasPropertyKey(type.properties, key)) {
      value[key] = (0, _from_type.FromType)(context, type.properties[key], value[key]);
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
} /* v9-17312416323ac2ad */
