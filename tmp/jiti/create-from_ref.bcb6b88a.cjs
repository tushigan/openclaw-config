"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromRef = FromRef;
var _index = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs");
var _error = require("./error.mjs"); // deno-fmt-ignore-file
function FromRef(context, type) {
  return _index.Guard.HasPropertyKey(context, type.$ref) ?
  (0, _from_type.FromType)(context, context[type.$ref]) :
  (() => {throw new _error.CreateError(type, 'Unable to deref Ref');})();
} /* v9-d394fc5fdf653853 */
