"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromCyclic = FromCyclic;
var _index = require("../../type/index.mjs");
var _from_type = require("./from_type.mjs");
var _callback = require("./callback.mjs"); // deno-fmt-ignore-file
function FromCyclic(direction, context, type, value) {
  value = (0, _from_type.FromType)(direction, { ...context, ...type.$defs }, (0, _index.Ref)(type.$ref), value);
  return (0, _callback.Callback)(direction, context, type, value);
} /* v9-c70c1d127856fc93 */
