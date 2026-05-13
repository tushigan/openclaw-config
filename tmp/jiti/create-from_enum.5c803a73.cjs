"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromEnum = FromEnum;
var _index = require("../../type/engine/enum/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromEnum(context, type) {
  return (0, _from_type.FromType)(context, (0, _index.EnumToUnion)(type));
} /* v9-1eba07460914f447 */
