"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromUnion = FromUnion;
var _index = require("../../schema/types/index.mjs");
var _index2 = require("../../type/index.mjs");
var _index3 = require("../../type/engine/evaluate/index.mjs");
var _index4 = require("../check/index.mjs");
var _index5 = require("../clone/index.mjs");
var _index6 = require("../create/index.mjs");
var _from_type = require("./from_type.mjs");
var _union_score_select = require("../shared/union_score_select.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// RepairUnion
// ------------------------------------------------------------------
function RepairUnion(context, type, value) {
  const union = (0, _index2.Union)((0, _index3.Flatten)(type.anyOf));
  const schema = (0, _union_score_select.UnionScoreSelect)(context, union, value);
  return (0, _from_type.FromType)(context, schema, value);
}
function FromUnion(context, type, value) {
  if ((0, _index4.Check)(context, type, value))
  return (0, _index5.Clone)(value);
  if ((0, _index.IsDefault)(type))
  return (0, _index6.Create)(context, type);
  return RepairUnion(context, type, value);
} /* v9-840bb5e628b4b6de */
