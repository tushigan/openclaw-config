"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsDefault = IsDefault;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid contentMediaType property
 * @specification Json Schema 7
 */
function IsDefault(schema) {
  return _index.Guard.HasPropertyKey(schema, 'default');
} /* v9-eed164b8f226896a */
