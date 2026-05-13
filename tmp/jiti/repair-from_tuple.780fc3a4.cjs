"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromTuple = FromTuple;
var _index = require("../../guard/index.mjs");
var _index2 = require("../check/index.mjs");
var _index3 = require("../create/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromTuple(context, schema, value) {
  if ((0, _index2.Check)(context, schema, value))
  return value;
  if (!_index.Guard.IsArray(value))
  return (0, _index3.Create)(context, schema);
  return schema.items.map((schema, index) => (0, _from_type.FromType)(context, schema, value[index]));
} /* v9-17413e0a4d02a07e */
