"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromInteger = FromInteger;
var _index = require("./try/index.mjs"); // deno-fmt-ignore-file
function FromInteger(_context, _type, value) {
  const result = _index.Try.TryNumber(value);
  return _index.Try.IsOk(result) ? Math.trunc(result.value) : value;
} /* v9-48f49b8982abdb39 */
