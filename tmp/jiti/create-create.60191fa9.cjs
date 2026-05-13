"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Create = Create;
var _index = require("../../system/arguments/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
/** Creates a value from the provided type. This function will use `default` annotations if present. */
function Create(...args) {
  const [context, type] = _index.Arguments.Match(args, {
    2: (context, type) => [context, type],
    1: (type) => [{}, type]
  });
  return (0, _from_type.FromType)(context, type);
} /* v9-32e43e9567f7d789 */
