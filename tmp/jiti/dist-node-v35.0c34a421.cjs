"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.URL = exports.DNS = void 0;exports.default = v35;exports.stringToBytes = stringToBytes;var _parse = _interopRequireDefault(require("./parse.js"));
var _stringify = require("./stringify.js");function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}
function stringToBytes(str) {
  str = unescape(encodeURIComponent(str));
  const bytes = new Uint8Array(str.length);
  for (let i = 0; i < str.length; ++i) {
    bytes[i] = str.charCodeAt(i);
  }
  return bytes;
}
const DNS = exports.DNS = '6ba7b810-9dad-11d1-80b4-00c04fd430c8';
const URL = exports.URL = '6ba7b811-9dad-11d1-80b4-00c04fd430c8';
function v35(version, hash, value, namespace, buf, offset) {
  const valueBytes = typeof value === 'string' ? stringToBytes(value) : value;
  const namespaceBytes = typeof namespace === 'string' ? (0, _parse.default)(namespace) : namespace;
  if (typeof namespace === 'string') {
    namespace = (0, _parse.default)(namespace);
  }
  if (namespace?.length !== 16) {
    throw TypeError('Namespace must be array-like (16 iterable integer values, 0-255)');
  }
  let bytes = new Uint8Array(16 + valueBytes.length);
  bytes.set(namespaceBytes);
  bytes.set(valueBytes, namespaceBytes.length);
  bytes = hash(bytes);
  bytes[6] = bytes[6] & 0x0f | version;
  bytes[8] = bytes[8] & 0x3f | 0x80;
  if (buf) {
    offset ??= 0;
    if (offset < 0 || offset + 16 > buf.length) {
      throw new RangeError(`UUID byte range ${offset}:${offset + 15} is out of buffer bounds`);
    }
    for (let i = 0; i < 16; ++i) {
      buf[offset + i] = bytes[i];
    }
    return buf;
  }
  return (0, _stringify.unsafeStringify)(bytes);
} /* v9-8bb8bc70e81c41dd */
