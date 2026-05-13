"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromObject = FromObject;

var _index = require("../../type/index.mjs");
var _index2 = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs");
var _index3 = require("../../schema/types/index.mjs"); // deno-fmt-ignore-file
// deno-lint-ignore-file
function FromObject(context, type, value) {if (!_index2.Guard.IsObject(value))
  return value;
  const knownPropertyKeys = _index2.Guard.Keys(type.properties);
  // Properties
  for (const key of knownPropertyKeys) {
    // Resolve Value for Property
    const propertyValue = (0, _from_type.FromType)(context, type.properties[key], value[key]);
    // Ambiguious Undefined: If the value is undefined, the type is optional there's no default. ignore.
    const isUnassignableUndefined = _index2.Guard.IsUndefined(propertyValue) && ((0, _index.IsOptional)(type.properties[key]) || !_index2.Guard.HasPropertyKey(type.properties[key], 'default'));
    if (isUnassignableUndefined)
    continue;
    // Assign
    value[key] = (0, _from_type.FromType)(context, type.properties[key], value[key]);
  }
  // return if not additional properties
  if (!(0, _index3.IsAdditionalProperties)(type) || _index2.Guard.IsBoolean(type.additionalProperties))
  return value;
  // AdditionalProperties
  for (const key of _index2.Guard.Keys(value)) {
    if (knownPropertyKeys.includes(key))
    continue;
    value[key] = (0, _from_type.FromType)(context, type.additionalProperties, value[key]);
  }
  return value;
} /* v9-3b93a4466cef9291 */
