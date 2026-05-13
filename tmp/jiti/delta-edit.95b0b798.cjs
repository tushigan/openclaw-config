"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Update = exports.Insert = exports.Edit = exports.Delete = void 0;
var T = _interopRequireWildcard(require("../../type/index.mjs"));function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);} // deno-fmt-ignore-file
const Insert = exports.Insert = T.Object({
  type: T.Literal('insert'),
  path: T.String(),
  value: T.Unknown()
});
const Update = exports.Update = Object({
  type: T.Literal('update'),
  path: T.String(),
  value: T.Unknown()
});
const Delete = exports.Delete = T.Object({
  type: T.Literal('delete'),
  path: T.String()
});
const Edit = exports.Edit = T.Union([Insert, Update, Delete]); /* v9-5e67877dd00b5024 */
