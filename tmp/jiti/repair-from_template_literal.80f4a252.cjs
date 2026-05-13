"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromTemplateLiteral = FromTemplateLiteral;
var _index = require("../../type/engine/template_literal/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromTemplateLiteral(context, type, value) {
  const decoded = (0, _index.TemplateLiteralDecode)(type.pattern);
  return (0, _from_type.FromType)(context, decoded, value);
} /* v9-8284dab7fcf5088e */
