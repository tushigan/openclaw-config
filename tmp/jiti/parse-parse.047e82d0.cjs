"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Parse = Parse;exports.Parser = exports.ParseError = void 0;
var _system = require("../../system/system.mjs");
var _index = require("../../system/arguments/index.mjs");
var _index2 = require("../assert/index.mjs");
var _index3 = require("../check/index.mjs");
var _index4 = require("../errors/index.mjs");
var _index5 = require("../clean/index.mjs");
var _index6 = require("../clone/index.mjs");
var _index7 = require("../convert/index.mjs");
var _index8 = require("../default/index.mjs");
var _index9 = require("../pipeline/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Assert
// ------------------------------------------------------------------
class ParseError extends _index2.AssertError {
  constructor(value, errors) {
    super('Parse', value, errors);
  }
}exports.ParseError = ParseError;
function Assert(context, type, value) {
  if (!(0, _index3.Check)(context, type, value))
  throw new ParseError(value, (0, _index4.Errors)(context, type, value));
  return value;
}
// ------------------------------------------------------------------
// Parser
// ------------------------------------------------------------------
const Parser = exports.Parser = (0, _index9.Pipeline)([
(_context, _type, value) => (0, _index6.Clone)(value),
(context, type, value) => (0, _index8.Default)(context, type, value),
(context, type, value) => (0, _index7.Convert)(context, type, value),
(context, type, value) => (0, _index5.Clean)(context, type, value),
(context, type, value) => Assert(context, type, value)]
);
/**  Parses a value with the given type. */
function Parse(...args) {
  const [context, type, value] = _index.Arguments.Match(args, {
    3: (context, type, value) => [context, type, value],
    2: (type, value) => [{}, type, value]
  });
  const checked = (0, _index3.Check)(context, type, value);
  if (checked)
  return value;
  if (_system.Settings.Get().correctiveParse)
  return Parser(context, type, value);
  throw new ParseError(value, (0, _index4.Errors)(context, type, value));
} /* v9-4b50b1000b9f5017 */
