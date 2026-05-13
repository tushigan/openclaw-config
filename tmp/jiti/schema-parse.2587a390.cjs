"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Parse = Parse;exports.ParseError = void 0;

var _index = require("../system/arguments/index.mjs");
var _check = require("./check.mjs");
var _errors = require("./errors.mjs"); // deno-fmt-ignore-file
// deno-lint-ignore-file
// ------------------------------------------------------------------
// ParseError
// ------------------------------------------------------------------
class ParseError {constructor(schema, value, errors) {
    this.schema = schema;
    this.value = value;
    this.errors = errors;
  }
}
/** Parses a value against the provided schema */exports.ParseError = ParseError;
function Parse(...args) {
  const [context, schema, value] = _index.Arguments.Match(args, {
    3: (context, schema, value) => [context, schema, value],
    2: (schema, value) => [{}, schema, value]
  });
  if (!(0, _check.Check)(context, schema, value)) {
    const [_result, errors] = (0, _errors.Errors)(context, schema, value);
    throw new ParseError(schema, value, errors);
  }
  return value;
} /* v9-b01500235a46ebcb */
