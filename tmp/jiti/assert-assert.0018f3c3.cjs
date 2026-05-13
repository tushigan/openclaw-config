"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Assert = Assert;exports.AssertError = void 0;
var _index = require("../../system/arguments/index.mjs");
var _index2 = require("../check/index.mjs");
var _index3 = require("../errors/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// AssertError
// ------------------------------------------------------------------
class AssertError extends Error {
  constructor(source, value, errors) {
    super(source);
    Object.defineProperty(this, 'cause', {
      value: { source, errors, value },
      writable: false,
      configurable: false,
      enumerable: false
    });
  }
}
/** Asserts the a value matches the given type. This function returns a TypeScript type asserts predicate and will throw AssertError if value does not match. */exports.AssertError = AssertError;
function Assert(...args) {
  const [context, type, value] = _index.Arguments.Match(args, {
    3: (context, type, value) => [context, type, value],
    2: (type, value) => [{}, type, value]
  });
  const check = (0, _index2.Check)(context, type, value);
  if (!check)
  throw new AssertError('Assert', value, (0, _index3.Errors)(context, type, value));
} /* v9-f7b7ba286d9c6b0a */
