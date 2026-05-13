"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromObject = FromObject;
var _index = require("../../guard/index.mjs");
var _index2 = require("../pointer/index.mjs");
var _index3 = require("../clone/index.mjs");
var _from_value = require("./from_value.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// AssertKey
// ------------------------------------------------------------------
function AssertKey(key) {
  if (_index.Guard.IsUnsafePropertyKey(key))
  throw Error('Attempted to Mutate with unsafe property key');
}
// ------------------------------------------------------------------
// AssertKey
// ------------------------------------------------------------------
function FromObject(root, path, current, next) {
  if (!_index.Guard.IsObjectNotArray(current)) {
    _index2.Pointer.Set(root, path, (0, _index3.Clone)(next));
  } else
  {
    const currentKeys = _index.Guard.Keys(current);
    const nextKeys = _index.Guard.Keys(next);
    for (const currentKey of currentKeys) {
      AssertKey(currentKey);
      if (!nextKeys.includes(currentKey)) {
        delete current[currentKey];
      }
    }
    for (const nextKey of nextKeys) {
      AssertKey(nextKey);
      if (!currentKeys.includes(nextKey)) {
        current[nextKey] = next[nextKey];
      }
    }
    for (const nextKey of nextKeys) {
      AssertKey(nextKey);
      (0, _from_value.FromValue)(root, `${path}/${nextKey}`, current[nextKey], next[nextKey]);
    }
  }
} /* v9-e6b6678385329bea */
