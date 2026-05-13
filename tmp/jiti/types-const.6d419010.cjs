"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsConst = IsConst;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid const property
 * @specification Json Schema 7
 */
function IsConst(value) {
  return _index.Guard.HasPropertyKey(value, 'const');
} /* v9-7c24a1e42525011c */
