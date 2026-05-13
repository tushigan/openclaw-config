"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromBigInt = FromBigInt;
var _index = require("./try/index.mjs"); // deno-fmt-ignore-file
function FromBigInt(_context, _type, value) {
  const result = _index.Try.TryBigInt(value);
  return _index.Try.IsOk(result) ? result.value : value;
} /* v9-fcefe011c8f72ce3 */
