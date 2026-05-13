"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromEnum = FromEnum;
var _index = require("../../type/engine/enum/index.mjs");
var _from_union = require("./from_union.mjs"); // deno-fmt-ignore-file
function FromEnum(context, type, value) {
  const union = (0, _index.EnumToUnion)(type);
  return (0, _from_union.FromUnion)(context, union, value);
} /* v9-2ac156b23f667fb2 */
