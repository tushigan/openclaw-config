"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.TryBoolean = TryBoolean;
var _index = require("../../../guard/index.mjs");
var _try_result = require("./try_result.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// BigInt
// ------------------------------------------------------------------
function FromBigInt(value) {
  return _index.Guard.IsEqual(value, BigInt(0)) ? (0, _try_result.Ok)(false) :
  _index.Guard.IsEqual(value, BigInt(1)) ? (0, _try_result.Ok)(true) :
  (0, _try_result.Fail)();
}
// ------------------------------------------------------------------
// Number
// ------------------------------------------------------------------
function FromNumber(value) {
  return _index.Guard.IsEqual(value, 0) ? (0, _try_result.Ok)(false) :
  _index.Guard.IsEqual(value, 1) ? (0, _try_result.Ok)(true) :
  (0, _try_result.Fail)();
}
// ------------------------------------------------------------------
// String
// ------------------------------------------------------------------
function FromString(value) {
  return _index.Guard.IsEqual(value.toLowerCase(), 'false') ? (0, _try_result.Ok)(false) :
  _index.Guard.IsEqual(value.toLowerCase(), 'true') ? (0, _try_result.Ok)(true) :
  _index.Guard.IsEqual(value, '0') ? (0, _try_result.Ok)(false) :
  _index.Guard.IsEqual(value, '1') ? (0, _try_result.Ok)(true) :
  (0, _try_result.Fail)();
}
// ------------------------------------------------------------------
// Try
// ------------------------------------------------------------------
function TryBoolean(value) {
  return _index.Guard.IsBigInt(value) ? FromBigInt(value) :
  _index.Guard.IsBoolean(value) ? (0, _try_result.Ok)(value) :
  _index.Guard.IsNumber(value) ? FromNumber(value) :
  _index.Guard.IsNull(value) ? (0, _try_result.Ok)(false) :
  _index.Guard.IsString(value) ? FromString(value) :
  _index.Guard.IsUndefined(value) ? (0, _try_result.Ok)(false) :
  (0, _try_result.Fail)();
} /* v9-2c3f75f6c0e0027f */
