"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromString = FromString;
var _index = require("./try/index.mjs"); // deno-fmt-ignore-file
function FromString(_context, _type, value) {
  const result = _index.Try.TryString(value);
  return _index.Try.IsOk(result) ? result.value : value;
} /* v9-ea29a18dfb2c8f3b */
