"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsDefs = IsDefs;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/** Returns true if the schema contains a valid $defs property */
function IsDefs(schema) {
  return _index.Guard.HasPropertyKey(schema, '$defs') &&
  _index.Guard.IsObject(schema.$defs) &&
  Object.values(schema.$defs).every((value) => (0, _schema.IsSchema)(value));
} /* v9-bca5aecb7017d05d */
