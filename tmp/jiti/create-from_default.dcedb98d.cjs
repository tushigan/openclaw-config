"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromDefault = FromDefault;
var _index = require("../../guard/index.mjs");
var _index2 = require("../clone/index.mjs"); // deno-fmt-ignore-file
function FromDefault(_context, schema) {
  return _index.Guard.IsFunction(schema.default) ?
  schema.default(schema) :
  _index.Guard.IsObject(schema.default) ?
  (0, _index2.Clone)(schema.default) :
  schema.default;
} /* v9-52ef16e5f3d702ce */
