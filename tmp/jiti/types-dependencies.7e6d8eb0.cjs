"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsDependencies = IsDependencies;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid dependencies property
 * @specification Json Schema 7
 */
function IsDependencies(schema) {
  return _index.Guard.HasPropertyKey(schema, 'dependencies') &&
  _index.Guard.IsObject(schema.dependencies) &&
  Object.values(schema.dependencies).every((value) => (0, _schema.IsSchema)(value) ||
  _index.Guard.IsArray(value) && value.every((value) => _index.Guard.IsString(value)));
} /* v9-8ef6a4fa29b5ae25 */
