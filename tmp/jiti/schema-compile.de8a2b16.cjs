"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Compile = Compile;exports.Validator = void 0;

var _index = require("../system/arguments/index.mjs");
var Build = _interopRequireWildcard(require("./build.mjs"));
var _errors = require("./errors.mjs");
var _parse = require("./parse.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// deno-lint-ignore-file
// ------------------------------------------------------------------
// Validator
// ------------------------------------------------------------------
class Validator {constructor(context, schema) {
    this.build = Build.Build(context, schema);
    this.result = this.build.Evaluate();
  }
  /** Returns true if this Validator is using JIT acceleration. */
  IsAccelerated() {
    return this.result.IsAccelerated;
  }
  /** Returns the underlying Schema used to construct this Validator. */
  Schema() {
    return this.build.Schema();
  }
  /** Performs a type-guard check on the provided value. */
  Check(value) {
    return this.result.Check(value);
  }
  /** Validates a value and returns it. Will throw if invalid. */
  Parse(value) {
    if (this.result.Check(value))
    return value;
    const [_result, errors] = (0, _errors.Errors)(this.build.Context(), this.build.Schema(), value);
    throw new _parse.ParseError(this.build.Schema(), value, errors);
  }
  /** Inspects a value and returns a detailed list of validation errors. */
  Errors(value) {
    return (0, _errors.Errors)(this.build.Context(), this.build.Schema(), value);
  }
}
/** Compiles this schema into a high performance Validator */exports.Validator = Validator;
function Compile(...args) {
  const [context, schema] = _index.Arguments.Match(args, {
    2: (context, schema) => [context, schema],
    1: (schema) => [{}, schema]
  });
  return new Validator(context, schema);
} /* v9-30d585b0625cdcc6 */
