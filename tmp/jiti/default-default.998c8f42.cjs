"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Default = Default;
var _index = require("../../system/arguments/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
/**
 * Patches missing properties on the value using default annotations specified on the provided type. This
 * function returns unknown so callers should Check the return value before use. This function mutates the
 * provided value. If mutation is not wanted, you should Clone the value before passing to this function.
 */
function Default(...args) {
  const [context, type, value] = _index.Arguments.Match(args, {
    3: (context, type, value) => [context, type, value],
    2: (type, value) => [{}, type, value]
  });
  return (0, _from_type.FromType)(context, type, value);
} /* v9-a760822adacf593c */
