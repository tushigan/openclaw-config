"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Validator = void 0;
var _index = require("../system/settings/index.mjs");
var _index2 = require("../system/arguments/index.mjs");
var _index3 = require("../system/environment/index.mjs");
var _index4 = require("../type/index.mjs");
var _index5 = require("../value/index.mjs");
var _index6 = require("../schema/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Validator<...>
// ------------------------------------------------------------------
class Validator extends _index4.Base {
  /** Constructs a Validator. */
  constructor(...args) {
    super();
    const matched = _index2.Arguments.Match(args, {
      6: (context, type, isEvalulated, hasCodec, code, check) => [context, type, isEvalulated, hasCodec, code, check],
      2: (context, type) => [context, type]
    });
    if (matched.length === 6) {
      const [context, type, isEvaluated, hasCodec, code, check] = matched;
      this.context = context;
      this.type = type;
      this.isAccelerated = isEvaluated;
      this.hasCodec = hasCodec;
      this.code = code;
      this.check = check;
    } else
    {
      const [context, type] = matched;
      const result = (0, _index6.Build)(context, type).Evaluate();
      this.hasCodec = (0, _index5.HasCodec)(context, type);
      this.context = context;
      this.type = type;
      this.isAccelerated = result.IsAccelerated;
      this.code = result.Code;
      this.check = result.Check;
    }
  }
  // ----------------------------------------------------------------
  // IsAccelerated
  // ----------------------------------------------------------------
  /** Returns true if this Validator is using JIT acceleration. */
  IsAccelerated() {
    return this.isAccelerated;
  }
  // ----------------------------------------------------------------
  // Context | Type
  // ----------------------------------------------------------------
  /** Returns the Context for this validator. */
  Context() {
    return this.context;
  }
  /** Returns the underlying Type used to construct this Validator. */
  Type() {
    return this.type;
  }
  // ----------------------------------------------------------------
  // Code
  // ----------------------------------------------------------------
  /** Returns the generated code for this validator. */
  Code() {
    return this.code;
  }
  // ----------------------------------------------------------------
  // Base<...>
  // ----------------------------------------------------------------
  /** Performs a type-guard check on the provided value. */
  Check(value) {
    return this.check(value);
  }
  /** Inspects a value and returns a detailed list of validation errors. */
  Errors(value) {
    if (_index3.Environment.CanEvaluate() && this.check(value))
    return [];
    return (0, _index5.Errors)(this.context, this.type, value);
  }
  /** Cleans a value using the Validator type. */
  Clean(value) {
    return (0, _index5.Clean)(this.context, this.type, value);
  }
  /** Converts a value using the Validator type. */
  Convert(value) {
    return (0, _index5.Convert)(this.context, this.type, value);
  }
  /** Creates a value using the Validator type. */
  Create() {
    return (0, _index5.Create)(this.context, this.type);
  }
  /** Creates defaults using the Validator type. */
  Default(value) {
    return (0, _index5.Default)(this.context, this.type, value);
  }
  /** Clones this validator. */
  Clone() {
    return new Validator(this.context, this.type, this.isAccelerated, this.hasCodec, this.code, this.check);
  }
  /** Validates a value and returns it. Will throw if invalid. */
  Parse(value) {
    const checked = this.Check(value);
    if (checked)
    return value;
    if (_index.Settings.Get().correctiveParse)
    return (0, _index5.Parser)(this.context, this.type, value);
    throw new _index5.ParseError(value, this.Errors(value));
  }
  /** Decodes a value */
  Decode(value) {
    const result = this.hasCodec ? (0, _index5.Decode)(this.context, this.type, value) : this.Parse(value);
    return result;
  }
  /** Encodes a value */
  Encode(value) {
    const result = this.hasCodec ? (0, _index5.Encode)(this.context, this.type, value) : this.Parse(value);
    return result;
  }
}exports.Validator = Validator; /* v9-eb76517bac8f415a */
