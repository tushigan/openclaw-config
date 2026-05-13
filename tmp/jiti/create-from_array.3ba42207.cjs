"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromArray = FromArray;
var _index = require("../../schema/types/index.mjs");
var _from_type = require("./from_type.mjs");
var _error = require("./error.mjs"); // deno-fmt-ignore-file
function FromArray(context, type) {
  if ((0, _index.IsUniqueItems)(type) && !(0, _index.IsDefault)(type))
  throw new _error.CreateError(type, 'Arrays with uniqueItems constraints must specify a default annotation');
  const length = (0, _index.IsMinItems)(type) ? type.minItems : 0;
  return Array.from({ length }, () => (0, _from_type.FromType)(context, type.items));
} /* v9-ea26f2741af9ef49 */
