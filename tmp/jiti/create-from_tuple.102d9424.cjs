"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromTuple = FromTuple;
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromTuple(context, type) {
  return Array.from({ length: type.minItems }, (_, i) => (0, _from_type.FromType)(context, type.items[i]));
} /* v9-a5632f0bc0f84eee */
