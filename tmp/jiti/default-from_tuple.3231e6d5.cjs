"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromTuple = FromTuple;

var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
// deno-lint-ignore-file
function FromTuple(context, schema, value) {if (!_index.Guard.IsArray(value))
  return value;
  const [items, max] = [schema.items, Math.max(schema.items.length, value.length)];
  for (let i = 0; i < max; i++) {
    if (i < items.length)
    value[i] = (0, _from_type.FromType)(context, items[i], value[i]);
  }
  return value;
} /* v9-a1cb13be9273cb3e */
