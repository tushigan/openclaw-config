"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromPromise = FromPromise;
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromPromise(context, type) {
  return Promise.resolve((0, _from_type.FromType)(context, type.item));
} /* v9-20608a1e56ffa5a1 */
