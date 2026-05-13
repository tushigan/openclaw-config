"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _rng = _interopRequireDefault(require("./rng.js"));
var _stringify = require("./stringify.js");function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
function v4(options, buf, offset) {
  if (!buf && !options && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return _v4(options, buf, offset);
}
function _v4(options, buf, offset) {
  options = options || {};
  const rnds = options.random ?? options.rng?.() ?? (0, _rng.default)();
  if (rnds.length < 16) {
    throw new Error('Random bytes length must be >= 16');
  }
  rnds[6] = rnds[6] & 0x0f | 0x40;
  rnds[8] = rnds[8] & 0x3f | 0x80;
  if (buf) {
    offset = offset || 0;
    if (offset < 0 || offset + 16 > buf.length) {
      throw new RangeError(`UUID byte range ${offset}:${offset + 15} is out of buffer bounds`);
    }
    for (let i = 0; i < 16; ++i) {
      buf[offset + i] = rnds[i];
    }
    return buf;
  }
  return (0, _stringify.unsafeStringify)(rnds);
}var _default = exports.default =
v4; /* v9-67129bd08fbebff7 */
