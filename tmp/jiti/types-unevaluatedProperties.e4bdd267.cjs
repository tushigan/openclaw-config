"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsUnevaluatedProperties = IsUnevaluatedProperties;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid unevaluatedProperties property
 * @specification Json Schema 2019-09
 */
function IsUnevaluatedProperties(schema) {
  return _index.Guard.HasPropertyKey(schema, 'unevaluatedProperties') &&
  (0, _schema.IsSchema)(schema.unevaluatedProperties);
} /* v9-256ea382d961ae64 */
