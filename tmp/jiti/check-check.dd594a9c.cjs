"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Check = Check;
var _index = require("../../system/arguments/index.mjs");
var _index2 = require("../../schema/index.mjs"); // deno-fmt-ignore-file
/** Checks a value matches the provided type. */
function Check(...args) {
  const [context, type, value] = _index.Arguments.Match(args, {
    3: (context, type, value) => [context, type, value],
    2: (type, value) => [{}, type, value]
  });
  return (0, _index2.Check)(context, type, value);
} /* v9-7563e55a5fb9637f */
