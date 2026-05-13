"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromTemplateLiteral = FromTemplateLiteral;
var _index = require("../../type/index.mjs");
var _index2 = require("../../type/engine/template_literal/index.mjs");
var _from_type = require("./from_type.mjs");
var _error = require("./error.mjs"); // deno-fmt-ignore-file
function FromTemplateLiteral(context, type) {
  const decoded = (0, _index2.TemplateLiteralDecode)(type.pattern);
  if ((0, _index.IsString)(decoded))
  throw new _error.CreateError(type, 'Unable to create TemplateLiteral due to infinite type expansion');
  return (0, _from_type.FromType)(context, decoded);
} /* v9-a7fe7e8201506eec */
