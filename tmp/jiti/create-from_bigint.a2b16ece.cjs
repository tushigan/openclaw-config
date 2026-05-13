"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromBigInt = FromBigInt;
var _index = require("../../schema/types/index.mjs"); // deno-fmt-ignore-file
function FromBigInt(_context, type) {
  return (0, _index.IsExclusiveMinimum)(type) ? BigInt(type.exclusiveMinimum) + BigInt(1) :
  (0, _index.IsMinimum)(type) ? BigInt(type.minimum) :
  BigInt(0);
} /* v9-70d7f2396c81a15a */
