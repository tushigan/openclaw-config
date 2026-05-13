"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Decode = Decode;exports.DecodeError = void 0;exports.DecodeUnsafe = DecodeUnsafe;
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
class DecodeError extends _index2.AssertError {
  constructor(value, errors) {
    super('Decode', value, errors);
  }
}exports.DecodeError = DecodeError;
function Assert(context, type, value) {
  if (!(0, _index3.Check)(context, type, value))
  throw new DecodeError(value, (0, _index4.Errors)(context, type, value));
  return value;
}
// ------------------------------------------------------------------
// DecodeUnsafe
// ------------------------------------------------------------------
/** Executes Decode callbacks only */
function DecodeUnsafe(context, type, value) {
  return (0, _from_type.FromType)('Decode', context, type, value);
}
// ------------------------------------------------------------------
// Decoder
// ------------------------------------------------------------------
const Decoder = (0, _index9.Pipeline)([
(_context, _type, value) => (0, _index6.Clone)(value),
(context, type, value) => (0, _index8.Default)(context, type, value),
(context, type, value) => (0, _index7.Convert)(context, type, value),
(context, type, value) => (0, _index5.Clean)(context, type, value),
(context, type, value) => Assert(context, type, value),
(context, type, value) => DecodeUnsafe(context, type, value)]
);
/** Decodes a value with the given type. */
function Decode(...args) {
  const [context, type, value] = _index.Arguments.Match(args, {
    3: (context, type, value) => [context, type, value],
    2: (type, value) => [{}, type, value]
  });
  return Decoder(context, type, value);
} /* v9-1d55c244ae254f9c */
