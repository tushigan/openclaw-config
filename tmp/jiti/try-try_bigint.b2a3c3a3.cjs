"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.TryBigInt = TryBigInt;
var _index = require("../../../guard/index.mjs");
var _try_result = require("./try_result.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Boolean
// ------------------------------------------------------------------
function FromBoolean(value) {
  return _index.Guard.IsEqual(value, true) ? (0, _try_result.Ok)(BigInt(1)) : (0, _try_result.Ok)(BigInt(0));
}
// ------------------------------------------------------------------
// String
// ------------------------------------------------------------------
const bigintPattern = /^-?(0|[1-9]\d*)n$/;
const decimalPattern = /^-?(0|[1-9]\d*)\.\d+$/;
const integerPattern = /^-?(0|[1-9]\d*)$/;
function IsStringBigIntLike(value) {
  return bigintPattern.test(value);
}
function IsStringDecimalLike(value) {
  return decimalPattern.test(value);
}
function IsStringIntegerLike(value) {
  return integerPattern.test(value);
}
function FromString(value) {
  const lowercase = value.toLowerCase();
  return IsStringBigIntLike(value) ? (0, _try_result.Ok)(BigInt(value.slice(0, value.length - 1))) :
  IsStringDecimalLike(value) ? (0, _try_result.Ok)(BigInt(value.split('.')[0])) :
  IsStringIntegerLike(value) ? (0, _try_result.Ok)(BigInt(value)) :
  _index.Guard.IsEqual(lowercase, 'false') ? (0, _try_result.Ok)(BigInt(0)) :
  _index.Guard.IsEqual(lowercase, 'true') ? (0, _try_result.Ok)(BigInt(1)) :
  (0, _try_result.Fail)();
}
// ------------------------------------------------------------------
// Try
// ------------------------------------------------------------------
function TryBigInt(value) {
  return _index.Guard.IsBigInt(value) ? (0, _try_result.Ok)(value) :
  _index.Guard.IsBoolean(value) ? FromBoolean(value) :
  _index.Guard.IsNumber(value) ? (0, _try_result.Ok)(BigInt(Math.trunc(value))) :
  _index.Guard.IsNull(value) ? (0, _try_result.Ok)(BigInt(0)) :
  _index.Guard.IsString(value) ? FromString(value) :
  _index.Guard.IsUndefined(value) ? (0, _try_result.Ok)(BigInt(0)) :
  (0, _try_result.Fail)();
} /* v9-a6893c6c9ffeca89 */
