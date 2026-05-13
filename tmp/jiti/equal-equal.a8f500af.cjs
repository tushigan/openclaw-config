"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Equal = Equal;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
/** Returns true if left and right values are structurally equal */
function Equal(left, right) {
  return _index.Guard.IsDeepEqual(left, right);
} /* v9-ed9a7571af50bf2b */
