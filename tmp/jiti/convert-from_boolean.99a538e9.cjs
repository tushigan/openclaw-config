"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromBoolean = FromBoolean;
var _index = require("./try/index.mjs"); // deno-fmt-ignore-file
function FromBoolean(_context, _type, value) {
  const result = _index.Try.TryBoolean(value);
  return _index.Try.IsOk(result) ? result.value : value;
} /* v9-29d2b9356b7501ea */
