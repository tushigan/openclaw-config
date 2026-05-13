"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsPrefixItems = IsPrefixItems;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid prefixItems property
 */
function IsPrefixItems(schema) {
  return _index.Guard.HasPropertyKey(schema, 'prefixItems') &&
  _index.Guard.IsArray(schema.prefixItems) &&
  schema.prefixItems.every((schema) => (0, _schema.IsSchema)(schema));
} /* v9-d7495d68b59c35bb */
