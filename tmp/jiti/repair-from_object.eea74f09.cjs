"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromObject = FromObject;
var _index = require("../../guard/index.mjs");
var _index2 = require("../check/index.mjs");
var _index3 = require("../create/index.mjs");
var _index4 = require("../../schema/types/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromObject(context, type, value) {
  if ((0, _index2.Check)(context, type, value))
  return value;
  if (!_index.Guard.IsObjectNotArray(value))
  return (0, _index3.Create)(context, type);
  // Dependencies
  const required = new Set(_index.Guard.IsUndefined(type.required) ? [] : type.required);
  // Properties
  const result = {};
  for (const [key, schema] of _index.Guard.Entries(type.properties)) {
    if (!required.has(key) && _index.Guard.IsUndefined(value[key]))
    continue;
    result[key] = key in value ?
    (0, _from_type.FromType)(context, schema, value[key]) :
    (0, _index3.Create)(context, schema);
  }
  // AdditionalProperties
  const evaluatedKeys = _index.Guard.Keys(type.properties);
  if ((0, _index4.IsAdditionalProperties)(type) && _index.Guard.IsObject(type.additionalProperties)) {
    for (const key of _index.Guard.Keys(value)) {
      if (evaluatedKeys.includes(key))
      continue;
      result[key] = (0, _from_type.FromType)(context, type.additionalProperties, value[key]);
    }
  }
  return result;
} /* v9-8afd9051cba39712 */
