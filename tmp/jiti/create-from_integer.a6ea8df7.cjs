"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromInteger = FromInteger;
var _index = require("../../guard/index.mjs");
var _index2 = require("../../schema/types/index.mjs"); // deno-fmt-ignore-file
function FromInteger(_context, type) {
  return (0, _index2.IsExclusiveMinimum)(type) && _index.Guard.IsNumber(type.exclusiveMinimum) ? type.exclusiveMinimum + 1 :
  (0, _index2.IsMinimum)(type) ? type.minimum :
  0;
} /* v9-b31e04bb5e23c595 */
