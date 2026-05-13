"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromRef = FromRef;
var _from_type = require("./from_type.mjs");
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
function FromRef(context, type, value) {
  return _index.Guard.HasPropertyKey(context, type.$ref) ?
  (0, _from_type.FromType)(context, context[type.$ref], value) :
  value;
} /* v9-0ae4946e7aa115e2 */
