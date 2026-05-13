"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromUnknown = FromUnknown;
var _index = require("../check/index.mjs");
var _index2 = require("../create/index.mjs");
var _index3 = require("../convert/index.mjs"); // deno-fmt-ignore-file
function FromUnknown(context, type, value) {
  if ((0, _index.Check)(context, type, value))
  return value;
  const converted = (0, _index3.Convert)(context, type, value);
  if ((0, _index.Check)(context, type, converted))
  return converted;
  return (0, _index2.Create)(context, type);
} /* v9-f09cd37008ac89c5 */
