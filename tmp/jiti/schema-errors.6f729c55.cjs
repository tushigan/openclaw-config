"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Errors = Errors;
var _index = require("../system/arguments/index.mjs");
var _index2 = require("../system/settings/index.mjs");
var _config = require("../system/locale/_config.mjs");
var _index3 = require("../guard/index.mjs");
var Engine = _interopRequireWildcard(require("./engine/index.mjs"));function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
/** Checks a value and returns validation errors */
function Errors(...args) {
  const [context, schema, value] = _index.Arguments.Match(args, {
    3: (context, schema, value) => [context, schema, value],
    2: (schema, value) => [{}, schema, value]
  });
  const settings = _index2.Settings.Get();
  const locale = (0, _config.Get)();
  const errors = [];
  const stack = new Engine.Stack(context, schema);
  const errorContext = new Engine.ErrorContext((error) => {
    if (_index3.Guard.IsGreaterEqualThan(errors.length, settings.maxErrors))
    return;
    return errors.push({ ...error, message: locale(error) });
  });
  const result = Engine.ErrorSchema(stack, errorContext, '#', '', schema, value);
  return [result, errors];
} /* v9-48f5656f200c1f80 */
