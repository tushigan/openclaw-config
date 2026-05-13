"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromArray = FromArray;

var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
// deno-lint-ignore-file
function FromArray(context, type, value) {if (!_index.Guard.IsArray(value))
  return value;
  for (let i = 0; i < value.length; i++) {
    value[i] = (0, _from_type.FromType)(context, type.items, value[i]);
  }
  return value;
} /* v9-79c2069d7d1a1db6 */
