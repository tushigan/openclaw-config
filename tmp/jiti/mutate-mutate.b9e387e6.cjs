"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Mutate = Mutate;
var _index = require("../../guard/index.mjs");
var _error = require("./error.mjs");
var _from_value = require("./from_value.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// IsNonMutableValue
// ------------------------------------------------------------------
function IsNonMutableValue(value) {
  return _index.GlobalsGuard.IsTypeArray(value) ||
  _index.GlobalsGuard.IsDate(value) ||
  _index.GlobalsGuard.IsMap(value) ||
  _index.GlobalsGuard.IsSet(value) ||
  _index.Guard.IsNumber(value) ||
  _index.Guard.IsString(value) ||
  _index.Guard.IsBoolean(value) ||
  _index.Guard.IsSymbol(value);
}
// ------------------------------------------------------------------
// IsTrueObject
// ------------------------------------------------------------------
function IsMismatchedValue(left, right) {
  return _index.Guard.IsObjectNotArray(left) && _index.Guard.IsArray(right) ||
  _index.Guard.IsArray(left) && _index.Guard.IsObjectNotArray(right);
}
// ------------------------------------------------------------------
// Mutate
// ------------------------------------------------------------------
/**
 * Performs a deep structural assignment, applying values from next to current while retaining internal references. This function
 * is written for use in infrastructure that interprets reference changes as a signal to perform some action (i.e. React redraw), this
 * function can mitigate this by applying mutable updates deep within a value, ensuring parent references are retained.
 *
 * @deprecated This function is being removed in the next version but will be retained as a reference under examples.
 */
function Mutate(current, next) {
  if (IsNonMutableValue(current) || IsNonMutableValue(next))
  throw new _error.MutateError('Only object and array types can be mutated at the root level');
  if (IsMismatchedValue(current, next))
  throw new _error.MutateError('Cannot assign due type mismatch of assignable values');
  (0, _from_value.FromValue)(current, '', current, next);
} /* v9-35dae1c0fff03591 */
