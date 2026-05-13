"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromNull = FromNull;
var _index = require("./try/index.mjs"); // deno-fmt-ignore-file
function FromNull(_context, _type, value) {
  const result = _index.Try.TryNull(value);
  return _index.Try.IsOk(result) ? result.value : value;
} /* v9-c0771f1e3ac45e81 */
