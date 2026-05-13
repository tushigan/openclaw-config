"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromValue = FromValue;
var _index = require("../../guard/index.mjs");
var _from_array = require("./from_array.mjs");
var _from_object = require("./from_object.mjs");
var _from_unknown = require("./from_unknown.mjs"); // deno-fmt-ignore-file
function FromValue(root, path, current, next) {
  if (_index.Guard.IsArray(next))
  return (0, _from_array.FromArray)(root, path, current, next);
  if (_index.Guard.IsObject(next))
  return (0, _from_object.FromObject)(root, path, current, next);
  return (0, _from_unknown.FromUnknown)(root, path, current, next);
} /* v9-a968384649eaa309 */
