"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Hash = Hash;
var _index = require("../../system/hashing/index.mjs"); // deno-fmt-ignore-file
/**
 * Computes a unique 64-bit hash of the specified value and returns the hex string representation. This
 * function internally uses a non-cryptographic FNV1A64 algorithm for hashing. Hashing is implemented
 * via structural traversal of the value.
 */
function Hash(value) {
  return _index.Hashing.Hash(value);
} /* v9-c1aab90af057b310 */
