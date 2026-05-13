"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Errors = Errors;
var _index = require("../../system/arguments/index.mjs");
var _index2 = require("../../schema/index.mjs"); // deno-fmt-ignore-file
/**
 * Performs an exhaustive Check on the specified value and reports any errors found.
 * If no errors are found, an empty array is returned. Unlike Check, this function
 * does not terminate at the first occurance of an error. For best performance, call
 * Check first and call Errors only if Check returns false.
 */
function Errors(...args) {
  const [context, type, value] = _index.Arguments.Match(args, {
    3: (context, type, value) => [context, type, value],
    2: (type, value) => [{}, type, value]
  });
  const [_, errors] = (0, _index2.Errors)(context, type, value);
  return errors;
} /* v9-a0b41c3a3908ef5d */
