"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromString = FromString;
var _index = require("../../schema/types/index.mjs"); // deno-fmt-ignore-file
function FromString(_context, type) {
  const needsDefault = ((0, _index.IsPattern)(type) || (0, _index.IsFormat)(type)) && !(0, _index.IsDefault)(type);
  if (needsDefault)
  throw Error('Strings with format or pattern constraints must specify default');
  const minLength = (0, _index.IsMinLength)(type) ? type.minLength : 0;
  return ''.padEnd(minLength);
} /* v9-8d901110b185216a */
