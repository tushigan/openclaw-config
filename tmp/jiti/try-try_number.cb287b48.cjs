"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.TryNumber = TryNumber;
var _index = require("../../../guard/index.mjs");
var _try_result = require("./try_result.mjs");
var _try_bigint = require("./try_bigint.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// BigInt
// ------------------------------------------------------------------
const maxBigInt = BigInt(Number.MAX_SAFE_INTEGER);
const minBigInt = BigInt(Number.MIN_SAFE_INTEGER);
function FromBigInt(value) {
  return value <= maxBigInt && value >= minBigInt ? (0, _try_result.Ok)(Number(value)) : (0, _try_result.Fail)();
}
function FromBoolean(value) {
  return (0, _try_result.Ok)(value ? 1 : 0);
}
// ------------------------------------------------------------------
// String
// ------------------------------------------------------------------
function FromString(value) {
  const coerced = +value;
  if (_index.Guard.IsNumber(coerced))
  return (0, _try_result.Ok)(coerced);
  const lowercase = value.toLowerCase();
  if (_index.Guard.IsEqual(lowercase, 'false'))
  return (0, _try_result.Ok)(0);
  if (_index.Guard.IsEqual(lowercase, 'true'))
  return (0, _try_result.Ok)(1);
  const result = (0, _try_bigint.TryBigInt)(value);
  if ((0, _try_result.IsOk)(result))
  return result.value <= maxBigInt && result.value >= minBigInt ? (0, _try_result.Ok)(Number(result.value)) : (0, _try_result.Fail)();
  return (0, _try_result.Fail)();
}
// ------------------------------------------------------------------
// Try
// ------------------------------------------------------------------
function TryNumber(value) {
  return _index.Guard.IsBigInt(value) ? FromBigInt(value) :
  _index.Guard.IsBoolean(value) ? FromBoolean(value) :
  _index.Guard.IsNumber(value) ? (0, _try_result.Ok)(value) :
  _index.Guard.IsNull(value) ? (0, _try_result.Ok)(0) :
  _index.Guard.IsString(value) ? FromString(value) :
  _index.Guard.IsUndefined(value) ? (0, _try_result.Ok)(0) :
  (0, _try_result.Fail)();
} /* v9-fdb45b88d7e551cd */
