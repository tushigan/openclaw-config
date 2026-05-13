"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromArray = FromArray;
var _from_type = require("./from_type.mjs");
var _index = require("./try/index.mjs"); // deno-fmt-ignore-file
function FromArray(context, type, value) {
  const result = _index.Try.TryArray(value);
  return result.value.map((value) => (0, _from_type.FromType)(context, type.items, value));
} /* v9-f76f44871439e692 */
