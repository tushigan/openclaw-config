"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Encode = Encode;exports.EncodeError = void 0;exports.EncodeUnsafe = EncodeUnsafe;
var _index = require("../../system/arguments/index.mjs");
var _index2 = require("../assert/index.mjs");
var _index3 = require("../check/index.mjs");
var _index4 = require("../errors/index.mjs");
var _index5 = require("../clean/index.mjs");
var _index6 = require("../clone/index.mjs");
var _index7 = require("../convert/index.mjs");
var _index8 = require("../default/index.mjs");
var _index9 = require("../pipeline/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Assert
// ------------------------------------------------------------------
class EncodeError extends _index2.AssertError {
  constructor(value, errors) {
    super('Encode', value, errors);
  }
}exports.EncodeError = EncodeError;
function Assert(context, type, value) {
  if (!(0, _index3.Check)(context, type, value))
  throw new EncodeError(value, (0, _index4.Errors)(context, type, value));
  return value;
}
// ------------------------------------------------------------------
// EncodeUnsafe
// ------------------------------------------------------------------
/** Executes Encode callbacks only */
function EncodeUnsafe(context, type, value) {
  return (0, _from_type.FromType)('Encode', context, type, value);
}
// ------------------------------------------------------------------
// Encoder
// ------------------------------------------------------------------
const Encoder = (0, _index9.Pipeline)([
(_context, _type, value) => (0, _index6.Clone)(value),
(context, type, value) => EncodeUnsafe(context, type, value),
(context, type, value) => (0, _index8.Default)(context, type, value),
(context, type, value) => (0, _index7.Convert)(context, type, value),
(context, type, value) => (0, _index5.Clean)(context, type, value),
(context, type, value) => Assert(context, type, value)]
);
/** Encodes a value with the given type. */
function Encode(...args) {
  const [context, type, value] = _index.Arguments.Match(args, {
    3: (context, type, value) => [context, type, value],
    2: (type, value) => [{}, type, value]
  });
  return Encoder(context, type, value);
} /* v9-4a98a721c93ce11a */
