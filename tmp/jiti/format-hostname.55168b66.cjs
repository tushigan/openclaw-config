"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsHostname = IsHostname;var Idna = _interopRequireWildcard(require("./_idna.mjs"));function _interopRequireWildcard(e, t) {if ("function" == typeof WeakMap) var r = new WeakMap(),n = new WeakMap();return (_interopRequireWildcard = function (e, t) {if (!t && e && e.__esModule) return e;var o,i,f = { __proto__: null, default: e };if (null === e || "object" != typeof e && "function" != typeof e) return f;if (o = t ? n : r) {if (o.has(e)) return o.get(e);o.set(e, f);}for (const t in e) "default" !== t && {}.hasOwnProperty.call(e, t) && ((i = (o = Object.defineProperty) && Object.getOwnPropertyDescriptor(e, t)) && (i.get || i.set) ? o(f, t, i) : f[t] = e[t]);return f;})(e, t);}
/**
 * Returns true if the value is a valid hostname.
 * @specification https://tools.ietf.org/html/rfc1123
 * @specification https://tools.ietf.org/html/rfc5891
 * @specification https://tools.ietf.org/html/rfc5892
 */
function IsHostname(value) {
  if (value.length === 0 || value.length > 253)
  return false;
  if (value.charCodeAt(value.length - 1) === 46)
  return false;
  for (const label of value.split('.')) {
    if (!Idna.IsLabel(label))
    return false;
  }
  return true;
} /* v9-f09fdfbee3ec827f */
