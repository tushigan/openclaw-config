"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = void 0;var _nodeCrypto = require("node:crypto");
function md5(bytes) {
  if (Array.isArray(bytes)) {
    bytes = Buffer.from(bytes);
  } else
  if (typeof bytes === 'string') {
    bytes = Buffer.from(bytes, 'utf8');
  }
  return (0, _nodeCrypto.createHash)('md5').update(bytes).digest();
}var _default = exports.default =
md5; /* v9-a938288832e2a6ae */
