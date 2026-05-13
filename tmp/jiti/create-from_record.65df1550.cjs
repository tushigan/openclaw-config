"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromRecord = FromRecord;
var _index = require("../../schema/types/index.mjs");
var _error = require("./error.mjs"); // deno-fmt-ignore-file
function FromRecord(_context, type) {
  if ((0, _index.IsMinProperties)(type) && !(0, _index.IsDefault)(type))
  throw new _error.CreateError(type, 'Record with the minProperties constraint must have a default annotation');
  return {};
} /* v9-61a2cd7c8008b3b0 */
