"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = rng;const rnds8 = new Uint8Array(16);
function rng() {
  return crypto.getRandomValues(rnds8);
} /* v9-c112f0c52b431f48 */
