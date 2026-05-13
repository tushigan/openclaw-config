"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.TryArray = TryArray;
var _index = require("../../../guard/index.mjs");
var _try_result = require("./try_result.mjs"); // deno-fmt-ignore-file
function TryArray(value) {
  return _index.Guard.IsArray(value) ? (0, _try_result.Ok)(value) : (0, _try_result.Ok)([value]);
} /* v9-ffe7972048999c49 */
