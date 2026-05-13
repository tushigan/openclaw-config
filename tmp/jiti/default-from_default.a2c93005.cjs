"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromDefault = FromDefault;

var _index = require("../../guard/index.mjs");
var _index2 = require("../clone/index.mjs"); // deno-fmt-ignore-file
// deno-lint-ignore-file
// ------------------------------------------------------------------
// FromDefault
// ------------------------------------------------------------------
function FromDefault(type, value) {// we only use defaults when values are undefined, exit early
  if (!_index.Guard.IsUndefined(value))
  return value;
  return _index.Guard.IsFunction(type.default) ? type.default() : (0, _index2.Clone)(type.default);
} /* v9-1f0650ec0bb6f70e */
