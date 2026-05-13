"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromVoid = FromVoid;
var _index = require("./try/index.mjs"); // deno-fmt-ignore-file
function FromVoid(_context, _type, value) {
  const result = _index.Try.TryUndefined(value);
  return _index.Try.IsOk(result) ? void 0 : value;
} /* v9-e72966b890cbb42e */
