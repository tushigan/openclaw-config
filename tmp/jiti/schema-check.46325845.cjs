"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Check = Check;

var _index = require("../system/arguments/index.mjs");
var Engine = _interopRequireWildcard(require("./engine/index.mjs"));function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
// deno-lint-ignore-file
/** Checks a value against the provided schema */function Check(...args) {
  const [context, schema, value] = _index.Arguments.Match(args, {
    3: (context, schema, value) => [context, schema, value],
    2: (schema, value) => [{}, schema, value]
  });
  const stack = new Engine.Stack(context, schema);
  const checkContext = new Engine.CheckContext();
  return Engine.CheckSchema(stack, checkContext, schema, value);
} /* v9-2537604d5a658ffc */
