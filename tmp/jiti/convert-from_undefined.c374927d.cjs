"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromUndefined = FromUndefined;
var _index = require("./try/index.mjs"); // deno-fmt-ignore-file
function FromUndefined(_context, _type, value) {
  const result = _index.Try.TryUndefined(value);
  return _index.Try.IsOk(result) ? result.value : value;
} /* v9-0969edc69eafda68 */
