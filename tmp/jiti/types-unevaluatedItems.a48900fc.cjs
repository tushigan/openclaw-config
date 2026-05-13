"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsUnevaluatedItems = IsUnevaluatedItems;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid unevaluatedItems property
 * @specification Json Schema 2019-09
 */
function IsUnevaluatedItems(schema) {
  return _index.Guard.HasPropertyKey(schema, 'unevaluatedItems') &&
  (0, _schema.IsSchema)(schema.unevaluatedItems);
} /* v9-f3b148b077ff5885 */
