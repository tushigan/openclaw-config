"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromUnknown = FromUnknown;
var _index = require("../pointer/index.mjs"); // deno-fmt-ignore-file
function FromUnknown(root, path, current, next) {
  if (current === next)
  return;
  _index.Pointer.Set(root, path, next);
} /* v9-e42bb32c2c50ddbe */
