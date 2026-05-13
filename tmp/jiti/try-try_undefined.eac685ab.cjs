"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.TryUndefined = TryUndefined;
var _index = require("../../../guard/index.mjs");
var _try_result = require("./try_result.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// BigInt
// ------------------------------------------------------------------
function FromBigInt(value) {
  return _index.Guard.IsEqual(value, BigInt(0)) ? (0, _try_result.Ok)(undefined) : (0, _try_result.Fail)();
}
// ------------------------------------------------------------------
// Boolean
// ------------------------------------------------------------------
function FromBoolean(value) {
  return _index.Guard.IsEqual(value, false) ? (0, _try_result.Ok)(undefined) : (0, _try_result.Fail)();
}
// ------------------------------------------------------------------
// Number
// ------------------------------------------------------------------
function FromNumber(value) {
  return _index.Guard.IsEqual(value, 0) ? (0, _try_result.Ok)(undefined) : (0, _try_result.Fail)();
}
// ------------------------------------------------------------------
// String
// ------------------------------------------------------------------
function FromString(value) {
  const lowercase = value.toLowerCase();
  const predicate = _index.Guard.IsEqual(lowercase, 'undefined') ||
  _index.Guard.IsEqual(lowercase, 'null') ||
  _index.Guard.IsEqual(value, '') ||
  _index.Guard.IsEqual(value, '0');
  return predicate ? (0, _try_result.Ok)(undefined) : (0, _try_result.Fail)();
}
// ------------------------------------------------------------------
// Try
// ------------------------------------------------------------------
function TryUndefined(value) {
  return _index.Guard.IsBigInt(value) ? FromBigInt(value) :
  _index.Guard.IsBoolean(value) ? FromBoolean(value) :
  _index.Guard.IsNumber(value) ? FromNumber(value) :
  _index.Guard.IsNull(value) ? (0, _try_result.Ok)(undefined) :
  _index.Guard.IsString(value) ? FromString(value) :
  _index.Guard.IsUndefined(value) ? (0, _try_result.Ok)(value) :
  (0, _try_result.Fail)();
} /* v9-cc4b95d2dbcfab45 */
