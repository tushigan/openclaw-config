"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromUnion = FromUnion;
var _index = require("../../guard/index.mjs");
var _index2 = require("../check/index.mjs");
var _index3 = require("../clone/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromUnion(context, type, value) {
  const matched = type.anyOf.some((type) => (0, _index2.Check)(context, type, value));
  if (matched)
  return value;
  const candidates = type.anyOf.map((type) => (0, _from_type.FromType)(context, type, (0, _index3.Clone)(value)));
  const selected = candidates.find((value) => (0, _index2.Check)(context, type, value));
  return _index.Guard.IsUndefined(selected) ? value : selected;
} /* v9-8dabfca0d8b30431 */
