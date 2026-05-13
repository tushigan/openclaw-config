"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromIntersect = FromIntersect;
var _index = require("../../type/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromIntersect(context, type) {
  const instantiated = (0, _index.Instantiate)(context, type);
  const evaluated = (0, _index.Evaluate)(instantiated);
  return (0, _from_type.FromType)(context, evaluated);
} /* v9-28f9f56daaaa618f */
