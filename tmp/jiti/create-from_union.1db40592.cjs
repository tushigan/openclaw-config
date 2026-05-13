"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromUnion = FromUnion;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromUnion(context, type) {
  if (_index.Guard.IsEqual(type.anyOf.length, 0)) {
    throw Error('Unable to create Union with no variants');
  }
  return (0, _from_type.FromType)(context, type.anyOf[0]);
} /* v9-3a7e7bb1f35d7a3c */
