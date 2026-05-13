"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromTuple = FromTuple;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromTuple(context, schema, value) {
  if (!_index.Guard.IsArray(value))
  return value;
  const length = Math.min(value.length, schema.items.length);
  for (let index = 0; index < length; index++) {
    value[index] = (0, _from_type.FromType)(context, schema.items[index], value[index]);
  }
  return _index.Guard.IsGreaterThan(value.length, length) ?
  value.slice(0, length) :
  value;
} /* v9-959febc4d16a0a10 */
