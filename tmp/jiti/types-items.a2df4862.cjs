"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsItems = IsItems;exports.IsItemsSized = IsItemsSized;exports.IsItemsUnsized = IsItemsUnsized;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid items property
 * @specification Json Schema 7
 */
function IsItems(schema) {
  return _index.Guard.HasPropertyKey(schema, 'items') && (
  (0, _schema.IsSchema)(schema.items) ||
  _index.Guard.IsArray(schema.items) &&
  schema.items.every((value) => {
    return (0, _schema.IsSchema)(value);
  }));
}
/** Returns true if this schema is a sized items variant */
function IsItemsSized(schema) {
  return IsItems(schema) && _index.Guard.IsArray(schema.items);
}
/** Returns true if this schema is a unsized items variant */
function IsItemsUnsized(schema) {
  return IsItems(schema) && !_index.Guard.IsArray(schema.items);
} /* v9-93940700fdac2989 */
