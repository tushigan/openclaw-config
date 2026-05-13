"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Pipeline = Pipeline;
var _index = require("../../system/arguments/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Pipeline
// ------------------------------------------------------------------
/** Creates a value processing pipeline. */
function Pipeline(pipeline) {
  return (...args) => {
    const [context, type, value] = _index.Arguments.Match(args, {
      3: (context, type, value) => [context, type, value],
      2: (type, value) => [{}, type, value]
    });
    return pipeline.reduce((result, func) => func(context, type, result), value);
  };
} /* v9-dd5e8286a13caa69 */
