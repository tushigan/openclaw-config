"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromObject = FromObject;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromObject(context, type) {
  const required = _index.Guard.IsUndefined(type.required) ? [] : type.required;
  return required.reduce((result, key) => {
    return { ...result, [key]: (0, _from_type.FromType)(context, type.properties[key]) };
  }, {});
} /* v9-7645526d02ae34a8 */
