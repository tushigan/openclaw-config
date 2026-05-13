"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsIf = IsIf;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid $id property
 * @specification Json Schema 7
 */
function IsIf(schema) {
  return _index.Guard.HasPropertyKey(schema, 'if') &&
  (0, _schema.IsSchema)(schema.if);
} /* v9-fda2ce48be6f7859 */
