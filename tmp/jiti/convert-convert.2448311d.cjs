"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Convert = Convert;
var _index = require("../../system/arguments/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
/**
 * Converts a value to the given type, coercing interior values if a reasonable conversion is possible. This
 * function returns unknown so callers should Check the return value before use. This function mutates the
 * provided value. If mutation is not wanted, you should Clone the value before passing to this function.
 */
function Convert(...args) {
  const [context, type, value] = _index.Arguments.Match(args, {
    3: (context, type, value) => [context, type, value],
    2: (type, value) => [{}, type, value]
  });
  return (0, _from_type.FromType)(context, type, value);
} /* v9-4b5b09b07f80f48a */
