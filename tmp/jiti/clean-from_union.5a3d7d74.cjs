"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromUnion = FromUnion;
var _index = require("../check/index.mjs");
var _index2 = require("../clone/index.mjs");
var _from_type = require("./from_type.mjs");
var _union_priority_sort = require("../shared/union_priority_sort.mjs"); // deno-fmt-ignore-file
function FromUnion(context, type, value) {
  for (const schema of (0, _union_priority_sort.UnionPrioritySort)(type.anyOf)) {
    const clean = (0, _from_type.FromType)(context, schema, (0, _index2.Clone)(value));
    if ((0, _index.Check)(context, schema, clean))
    return clean;
  }
  return value;
} /* v9-f30a401bc7c1abed */
