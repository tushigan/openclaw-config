"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromEnum = FromEnum;
var _index = require("../../type/engine/enum/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromEnum(context, type, value) {
  const union = (0, _index.EnumToUnion)(type);
  return (0, _from_type.FromType)(context, union, value);
} /* v9-c7183f21d0abe457 */
