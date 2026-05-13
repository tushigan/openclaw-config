"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _validate = _interopRequireDefault(require("./validate.js"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
function parse(uuid) {
  if (!(0, _validate.default)(uuid)) {
    throw TypeError('Invalid UUID');
  }
  let v;
  return Uint8Array.of((v = parseInt(uuid.slice(0, 8), 16)) >>> 24, v >>> 16 & 0xff, v >>> 8 & 0xff, v & 0xff, (v = parseInt(uuid.slice(9, 13), 16)) >>> 8, v & 0xff, (v = parseInt(uuid.slice(14, 18), 16)) >>> 8, v & 0xff, (v = parseInt(uuid.slice(19, 23), 16)) >>> 8, v & 0xff, (v = parseInt(uuid.slice(24, 36), 16)) / 0x10000000000 & 0xff, v / 0x100000000 & 0xff, v >>> 24 & 0xff, v >>> 16 & 0xff, v >>> 8 & 0xff, v & 0xff);
}var _default = exports.default =
parse; /* v9-8aa06dfedbac2306 */
