"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Clean = Clean;var _index = require("../../system/arguments/index.mjs");
var _from_type = require("./from_type.mjs");
/**
 * Cleans a value by removing non-evaluated properties and elements as derived from the provided type.
 * This function returns unknown so callers should Check the return value before use. This function
 * mutates the provided value. If mutation is not wanted, you should Clone the value before passing
 * to this function.
 */
function Clean(...args) {
  const [context, type, value] = _index.Arguments.Match(args, {
    3: (context, type, value) => [context, type, value],
    2: (type, value) => [{}, type, value]
  });
  return (0, _from_type.FromType)(context, type, value);
} /* v9-641ae36b751c7e56 */
