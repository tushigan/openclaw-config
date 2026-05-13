"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.TryString = TryString;
var _index = require("../../../guard/index.mjs");
var _try_result = require("./try_result.mjs"); // deno-fmt-ignore-file
function TryString(value) {
  return _index.Guard.IsBigInt(value) ? (0, _try_result.Ok)(value.toString()) :
  _index.Guard.IsBoolean(value) ? (0, _try_result.Ok)(value.toString()) :
  _index.Guard.IsNumber(value) ? (0, _try_result.Ok)(value.toString()) :
  _index.Guard.IsNull(value) ? (0, _try_result.Ok)('null') :
  _index.Guard.IsString(value) ? (0, _try_result.Ok)(value) :
  _index.Guard.IsUndefined(value) ? (0, _try_result.Ok)('') :
  (0, _try_result.Fail)();
} /* v9-6a514686631223c6 */
