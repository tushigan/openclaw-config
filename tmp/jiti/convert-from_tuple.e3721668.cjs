"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromTuple = FromTuple;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromTuple(context, type, value) {
  if (!_index.Guard.IsArray(value))
  return value;
  for (let index = 0; index < Math.min(type.items.length, value.length); index++) {
    value[index] = (0, _from_type.FromType)(context, type.items[index], value[index]);
  }
  return value;
} /* v9-26708477a824aac7 */
