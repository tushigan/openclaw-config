"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromArray = FromArray;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromArray(context, type, value) {
  if (!_index.Guard.IsArray(value))
  return value;
  return value.map((value) => (0, _from_type.FromType)(context, type.items, value));
} /* v9-dd05ba4ca75c563c */
