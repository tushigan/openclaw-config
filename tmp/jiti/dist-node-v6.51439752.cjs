"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _stringify = require("./stringify.js");
var _v = _interopRequireDefault(require("./v1.js"));
var _v1ToV = _interopRequireDefault(require("./v1ToV6.js"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
function v6(options, buf, offset) {
  options ??= {};
  offset ??= 0;
  let bytes = (0, _v.default)({ ...options, _v6: true }, new Uint8Array(16));
  bytes = (0, _v1ToV.default)(bytes);
  if (buf) {
    if (offset < 0 || offset + 16 > buf.length) {
      throw new RangeError(`UUID byte range ${offset}:${offset + 15} is out of buffer bounds`);
    }
    for (let i = 0; i < 16; i++) {
      buf[offset + i] = bytes[i];
    }
    return buf;
  }
  return (0, _stringify.unsafeStringify)(bytes);
}var _default = exports.default =
v6; /* v9-704fce57fed77fb7 */
