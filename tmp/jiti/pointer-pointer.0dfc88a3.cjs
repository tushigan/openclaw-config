"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Delete = Delete;exports.Get = Get;exports.Has = Has;exports.Indices = Indices;exports.Set = Set;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Asserts
// ------------------------------------------------------------------
function AssertNotRoot(indices) {
  if (indices.length === 0)
  throw Error('Cannot set root');
}
function AssertCanSet(value) {
  if (!_index.Guard.IsObject(value))
  throw Error('Cannot set value');
}
function AssertIndex(index) {
  if (_index.Guard.IsUnsafePropertyKey(index))
  throw Error('Pointer contains unsafe property key');
}
function AssertIndices(indices) {
  for (const index of indices)
  AssertIndex(index);
}
// ------------------------------------------------------------------
// Indices
// ------------------------------------------------------------------
function IsNumericIndex(index) {
  return /^(0|[1-9]\d*)$/.test(index);
}
function TakeIndexRight(indices) {
  return [
  indices.slice(0, indices.length - 1),
  indices.slice(indices.length - 1)[0]];

}
function HasIndex(index, value) {
  return _index.Guard.IsObject(value) && _index.Guard.HasPropertyKey(value, index);
}
function GetIndex(index, value) {
  return _index.Guard.IsObject(value) && !_index.Guard.IsUnsafePropertyKey(index) ? value[index] : undefined;
}
function GetIndices(indices, value) {
  return indices.reduce((value, index) => GetIndex(index, value), value);
}
// ------------------------------------------------------------------
// Indices
// ------------------------------------------------------------------
/** Returns an array of path indices for the given pointer */
function Indices(pointer) {
  if (_index.Guard.IsEqual(pointer.length, 0))
  return [];
  const indices = pointer.split("/").map((index) => index.replace(/~1/g, "/").replace(/~0/g, "~"));
  return indices.length > 0 && indices[0] === '' ? indices.slice(1) : indices;
}
// ------------------------------------------------------------------
// Has
// ------------------------------------------------------------------
/** Returns true if a value exists at the current pointer */
function Has(value, pointer) {
  let current = value;
  return Indices(pointer).every((index) => {
    if (!HasIndex(index, current))
    return false;
    current = current[index];
    return true;
  });
}
// ------------------------------------------------------------------
// Get
// ------------------------------------------------------------------
/** Gets a value at the pointer, or undefined if not exists */
function Get(value, pointer) {
  const indices = Indices(pointer);
  return GetIndices(indices, value);
}
// ------------------------------------------------------------------
// Set
// ------------------------------------------------------------------
/** Sets a value at the given pointer. May throw if the target value is not indexable */
function Set(value, pointer, next) {
  const indices = Indices(pointer);
  AssertNotRoot(indices);
  AssertIndices(indices);
  const [head, index] = TakeIndexRight(indices);
  const parent = GetIndices(head, value);
  AssertCanSet(parent);
  parent[index] = next;
  return value;
}
// ------------------------------------------------------------------
// Delete
// ------------------------------------------------------------------
/** Deletes the value at the given pointer. May throw if the target value is not indexable */
function Delete(value, pointer) {
  const indices = Indices(pointer);
  AssertNotRoot(indices);
  AssertIndices(indices);
  const [head, index] = TakeIndexRight(indices);
  const parent = GetIndices(head, value);
  AssertCanSet(parent);
  if (_index.Guard.IsArray(parent) && IsNumericIndex(index)) {
    parent.splice(+index, 1);
  } else
  {
    delete parent[index];
  }
  return value;
} /* v9-c88b43b3a4c0b247 */
