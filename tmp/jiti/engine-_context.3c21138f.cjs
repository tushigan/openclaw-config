"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.ErrorContext = exports.CheckContext = exports.BuildContext = exports.AccumulatedErrorContext = void 0;exports.HasUnevaluated = HasUnevaluated;
var Schema = _interopRequireWildcard(require("../types/index.mjs"));
var _index2 = require("../../guard/index.mjs");function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// ------------------------------------------------------------------
// HasUnevaluated
// ------------------------------------------------------------------
function HasUnevaluatedFromObject(value) {
  return Schema.IsUnevaluatedItems(value) ||
  Schema.IsUnevaluatedProperties(value) ||
  _index2.Guard.Keys(value).some((key) => HasUnevaluatedFromUnknown(value[key]));
}
function HasUnevaluatedFromArray(value) {
  return value.some((value) => HasUnevaluatedFromUnknown(value));
}
function HasUnevaluatedFromUnknown(value) {
  return _index2.Guard.IsArray(value) ? HasUnevaluatedFromArray(value) :
  _index2.Guard.IsObject(value) ? HasUnevaluatedFromObject(value) :
  false;
}
function HasUnevaluated(context, schema) {
  return HasUnevaluatedFromUnknown(schema) || _index2.Guard.Keys(context).some((key) => HasUnevaluatedFromUnknown(context[key]));
}
// ------------------------------------------------------------------
// BuildContext
// ------------------------------------------------------------------
class BuildContext {
  constructor(hasUnevaluated) {
    this.hasUnevaluated = hasUnevaluated;
  }
  UseUnevaluated() {
    return this.hasUnevaluated;
  }
  // ----------------------------------------------------------------
  // Stack
  // ----------------------------------------------------------------
  Push() {
    return _index2.EmitGuard.Call(_index2.EmitGuard.Member('context', 'Push'), []);
  }
  Pop() {
    return _index2.EmitGuard.Call(_index2.EmitGuard.Member('context', 'Pop'), []);
  }
  // ----------------------------------------------------------------
  // Top
  // ----------------------------------------------------------------
  AddIndex(index) {
    return _index2.EmitGuard.Call(_index2.EmitGuard.Member('context', 'AddIndex'), [index]);
  }
  AddKey(key) {
    return _index2.EmitGuard.Call(_index2.EmitGuard.Member('context', 'AddKey'), [key]);
  }
  Merge(results) {
    return _index2.EmitGuard.Call(_index2.EmitGuard.Member('context', 'Merge'), [results]);
  }
}
// ------------------------------------------------------------------
// CheckContext
// ------------------------------------------------------------------
exports.BuildContext = BuildContext;class CheckContext {
  constructor() {
    const indices = new Set();
    const keys = new Set();
    this.stack = [{ indices, keys }];
  }
  // ----------------------------------------------------------------
  // Stack
  // ----------------------------------------------------------------
  Push() {
    const indices = new Set();
    const keys = new Set();
    this.stack.push({ indices, keys });
    return true;
  }
  Pop() {
    this.stack.pop();
    return true;
  }
  // ----------------------------------------------------------------
  // Top
  // ----------------------------------------------------------------
  AddIndex(index) {
    this.GetIndices().add(index);
    return true;
  }
  AddKey(key) {
    this.GetKeys().add(key);
    return true;
  }
  GetIndices() {
    const top = this.stack[this.stack.length - 1];
    return top.indices;
  }
  GetKeys() {
    const top = this.stack[this.stack.length - 1];
    return top.keys;
  }
  Merge(results) {
    for (const context of results) {
      context.GetIndices().forEach((value) => this.GetIndices().add(value));
      context.GetKeys().forEach((value) => this.GetKeys().add(value));
    }
    return true;
  }
}exports.CheckContext = CheckContext;
class ErrorContext extends CheckContext {
  constructor(callback) {
    super();
    this.callback = callback;
  }
  AddError(error) {
    this.callback(error);
    return false;
  }
}
// ------------------------------------------------------------------
// AccumulatedErrorContext
// ------------------------------------------------------------------
exports.ErrorContext = ErrorContext;class AccumulatedErrorContext extends ErrorContext {
  constructor() {
    super((error) => this.errors.push(error));
    this.errors = [];
  }
  AddError(error) {
    this.errors.push(error);
    return false;
  }
  GetErrors() {
    return this.errors;
  }
}exports.AccumulatedErrorContext = AccumulatedErrorContext; /* v9-bd5e031530705496 */
