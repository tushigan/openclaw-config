"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromLiteral = FromLiteral;
var _index = require("../../system/unreachable/index.mjs");
var _index2 = require("../../guard/index.mjs");
var _index3 = require("../../type/index.mjs");
var _index4 = require("./try/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// BigInt
// ------------------------------------------------------------------
function FromLiteralBigInt(_context, type, value) {
  const result = _index4.Try.TryBigInt(value);
  return _index4.Try.IsOk(result) && _index2.Guard.IsEqual(type.const, result.value) ? result.value : value;
}
// ------------------------------------------------------------------
// Boolean
// ------------------------------------------------------------------
function FromLiteralBoolean(_context, type, value) {
  const result = _index4.Try.TryBoolean(value);
  return _index4.Try.IsOk(result) && _index2.Guard.IsEqual(type.const, result.value) ? result.value : value;
}
// ------------------------------------------------------------------
// Number
// ------------------------------------------------------------------
function FromLiteralNumber(_context, type, value) {
  const result = _index4.Try.TryNumber(value);
  return _index4.Try.IsOk(result) && _index2.Guard.IsEqual(type.const, result.value) ? result.value : value;
}
// ------------------------------------------------------------------
// String
// ------------------------------------------------------------------
function FromLiteralString(_context, type, value) {
  const result = _index4.Try.TryString(value);
  return _index4.Try.IsOk(result) && _index2.Guard.IsEqual(type.const, result.value) ? result.value : value;
}
// deno-coverage-ignore-start - unreachable | guarded
function FromLiteral(context, type, value) {
  if (_index2.Guard.IsEqual(type.const, value))
  return value;
  return (0, _index3.IsLiteralBigInt)(type) ? FromLiteralBigInt(context, type, value) :
  (0, _index3.IsLiteralBoolean)(type) ? FromLiteralBoolean(context, type, value) :
  (0, _index3.IsLiteralNumber)(type) ? FromLiteralNumber(context, type, value) :
  (0, _index3.IsLiteralString)(type) ? FromLiteralString(context, type, value) :
  (0, _index.Unreachable)();
}
// deno-coverage-ignore-stop /* v9-aeca34295f8d9622 */
