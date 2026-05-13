"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _nodeCrypto = require("node:crypto");
function sha1(bytes) {
  if (Array.isArray(bytes)) {
    bytes = Buffer.from(bytes);
  } else
  if (typeof bytes === 'string') {
    bytes = Buffer.from(bytes, 'utf8');
  }
  return (0, _nodeCrypto.createHash)('sha1').update(bytes).digest();
}var _default = exports.default =
sha1; /* v9-6ceff708ee61c56f */
