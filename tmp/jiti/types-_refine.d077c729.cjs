"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsRefine = IsRefine;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains an '~refine` keyword
 * @specification None
 */
function IsRefine(value) {
  return _index.Guard.HasPropertyKey(value, '~refine') &&
  _index.Guard.IsArray(value["~refine"]) &&
  _index.Guard.Every(value['~refine'], 0, (value) => _index.Guard.IsObject(value) &&
  _index.Guard.HasPropertyKey(value, 'check') &&
  _index.Guard.HasPropertyKey(value, 'error') &&
  _index.Guard.IsFunction(value.check) &&
  _index.Guard.IsFunction(value.error));
} /* v9-ce253e73e3352e14 */
