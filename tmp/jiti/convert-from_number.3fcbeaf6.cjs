"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromNumber = FromNumber;
var _index = require("./try/index.mjs"); // deno-fmt-ignore-file
function FromNumber(_context, _type, value) {
  const result = _index.Try.TryNumber(value);
  return _index.Try.IsOk(result) ? result.value : value;
} /* v9-a3112e2e1114c324 */
