"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Compile = Compile;

var _index = require("../system/arguments/index.mjs");
var _validator = require("./validator.mjs"); // deno-lint-ignore-file ban-types
// deno-fmt-ignore-file
/** Compiles a type into a high performance Validator */function Compile(...args) {
  const [context, type] = _index.Arguments.Match(args, {
    2: (context, type) => [context, type],
    1: (type) => [{}, type]
  });
  return new _validator.Validator(context, type);
} /* v9-dc9d86aa5257d5e7 */
