"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromRef = FromRef;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromRef(context, type, value) {
  return _index.Guard.HasPropertyKey(context, type.$ref) ?
  (0, _from_type.FromType)(context, context[type.$ref], value) :
  value;
} /* v9-ecbe3c98f0412bdd */
