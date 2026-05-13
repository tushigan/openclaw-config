"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Clone = Clone;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// ClassInstance
//
// TypeBox does not support cloning arbitrary class instances. It treats
// class instances as atomic values, similar to number, boolean, and
// string. In the future, an implementation could detect the presence of
// a .clone() method, but no formal specification for this behavior
// exists, so we don't.
//
// ------------------------------------------------------------------
function FromClassInstance(value) {
  return value; // atomic
}
// ------------------------------------------------------------------
// ObjectInstance
// ------------------------------------------------------------------
function FromObjectInstance(value) {
  const result = {};
  for (const key of _index.Guard.Keys(value)) {
    if (_index.Guard.IsUnsafePropertyKey(key))
    continue; // (ignore: prototype-pollution)
    result[key] = Clone(value[key]);
  }
  for (const key of _index.Guard.Symbols(value)) {
    result[key] = Clone(value[key]);
  }
  return result;
}
// ------------------------------------------------------------------
// Object
// ------------------------------------------------------------------
function FromObject(value) {
  return _index.Guard.IsClassInstance(value) ?
  FromClassInstance(value) :
  FromObjectInstance(value);
}
// ------------------------------------------------------------------
// Array
// ------------------------------------------------------------------
function FromArray(value) {
  return value.map((element) => Clone(element));
}
// ------------------------------------------------------------------
// TypeArray
// ------------------------------------------------------------------
function FromTypedArray(value) {
  return value.slice();
}
// ------------------------------------------------------------------
// Map
// ------------------------------------------------------------------
function FromMap(value) {
  return new Map(Clone([...value.entries()]));
}
// ------------------------------------------------------------------
// Set
// ------------------------------------------------------------------
function FromSet(value) {
  return new Set(Clone([...value.values()]));
}
// ------------------------------------------------------------------
// Value
// ------------------------------------------------------------------
function FromValue(value) {
  return value;
}
// ------------------------------------------------------------------
// Clone
// ------------------------------------------------------------------
/**
 * Returns a Clone of the given value. This function is similar to structuredClone()
 * but also supports deep cloning instances of Map, Set and TypeArray.
 */
function Clone(value) {
  return _index.GlobalsGuard.IsTypeArray(value) ? FromTypedArray(value) :
  _index.GlobalsGuard.IsMap(value) ? FromMap(value) :
  _index.GlobalsGuard.IsSet(value) ? FromSet(value) :
  _index.Guard.IsArray(value) ? FromArray(value) :
  _index.Guard.IsObject(value) ? FromObject(value) :
  FromValue(value);
} /* v9-f382dbb0a34b6888 */
