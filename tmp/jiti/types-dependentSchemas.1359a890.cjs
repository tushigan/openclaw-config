"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsDependentSchemas = IsDependentSchemas;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid dependentRequired property
 * @specification Json Schema 2019-09
 */
function IsDependentSchemas(schema) {
  return _index.Guard.HasPropertyKey(schema, 'dependentSchemas') &&
  _index.Guard.IsObject(schema.dependentSchemas) &&
  Object.values(schema.dependentSchemas).every((value) => (0, _schema.IsSchema)(value));
} /* v9-112a775454201c9b */
