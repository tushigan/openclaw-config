"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromNever = FromNever;
var _error = require("./error.mjs"); // deno-fmt-ignore-file
function FromNever(_context, type) {
  throw new _error.CreateError(type, 'Cannot create TNever types');
} /* v9-96d76599c88177ba */
