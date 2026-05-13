"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsNot = IsNot;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid not property
 * @specification Json Schema 7
 */
function IsNot(schema) {
  return _index.Guard.HasPropertyKey(schema, 'not') &&
  (0, _schema.IsSchema)(schema.not);
} /* v9-6cf8f13111157ad6 */
