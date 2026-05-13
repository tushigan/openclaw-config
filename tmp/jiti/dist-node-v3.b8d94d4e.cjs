"use strict";Object.defineProperty(exports, "__esModule", { value: true });Object.defineProperty(exports, "DNS", { enumerable: true, get: function () {return _v.DNS;} });Object.defineProperty(exports, "URL", { enumerable: true, get: function () {return _v.URL;} });exports.default = void 0;var _md = _interopRequireDefault(require("./md5.js"));
var _v = _interopRequireWildcard(require("./v35.js"));function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}

function v3(value, namespace, buf, offset) {
  return (0, _v.default)(0x30, _md.default, value, namespace, buf, offset);
}
v3.DNS = _v.DNS;
v3.URL = _v.URL;var _default = exports.default =
v3; /* v9-f2e9ca37a7fe0734 */
