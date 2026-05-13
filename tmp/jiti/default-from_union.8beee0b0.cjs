"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromUnion = FromUnion;

var _index = require("../check/index.mjs");
var _index2 = require("../clone/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
// deno-lint-ignore-file
function FromUnion(context, schema, value) {for (const inner of schema.anyOf) {
    const result = (0, _from_type.FromType)(context, inner, (0, _index2.Clone)(value));
    if ((0, _index.Check)(context, inner, result)) {
      return result;
    }
  }
  return value;
} /* v9-ae138515c364cdd4 */
