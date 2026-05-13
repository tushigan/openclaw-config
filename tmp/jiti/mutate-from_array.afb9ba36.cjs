"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromArray = FromArray;
var _index = require("../../guard/index.mjs");
var _index2 = require("../clone/index.mjs");
var _index3 = require("../pointer/index.mjs");
var _from_value = require("./from_value.mjs"); // deno-fmt-ignore-file
function FromArray(root, path, current, next) {
  if (!_index.Guard.IsArray(current)) {
    _index3.Pointer.Set(root, path, (0, _index2.Clone)(next));
  } else
  {
    for (let index = 0; index < next.length; index++) {
      (0, _from_value.FromValue)(root, `${path}/${index}`, current[index], next[index]);
    }
    current.splice(next.length);
  }
} /* v9-5d0c9f7e95851b59 */
