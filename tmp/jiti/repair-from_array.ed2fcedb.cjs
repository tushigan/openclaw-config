"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromArray = FromArray;
var _index = require("../../schema/types/index.mjs");
var _index2 = require("../../guard/index.mjs");
var _index3 = require("../check/index.mjs");
var _index4 = require("../create/index.mjs");
var _index5 = require("../hash/index.mjs");
var _from_type = require("./from_type.mjs");
var _error = require("./error.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// MakeUnique
// ------------------------------------------------------------------
function MakeUnique(values) {
  const [hashes, result] = [new Set(), []];
  for (const value of values) {
    const hash = (0, _index5.Hash)(value);
    if (hashes.has(hash))
    continue;
    hashes.add(hash);
    result.push(value);
  }
  return result;
}
// ------------------------------------------------------------------
// FromArray
// ------------------------------------------------------------------
function FromArray(context, type, value) {
  if ((0, _index3.Check)(context, type, value))
  return value;
  const created = _index2.Guard.IsArray(value) ? value : (0, _index4.Create)(context, type);
  const minimum = (0, _index.IsMinItems)(type) && created.length < type.minItems ? [...created, ...Array.from({ length: type.minItems - created.length }, () => (0, _index4.Create)(context, type))] : created;
  const maximum = (0, _index.IsMaxItems)(type) && minimum.length > type.maxItems ? minimum.slice(0, type.maxItems) : minimum;
  const repaired = maximum.map((value) => (0, _from_type.FromType)(context, type.items, value));
  if (!(0, _index.IsUniqueItems)(type) || (0, _index.IsUniqueItems)(type) && !_index2.Guard.IsEqual(type.uniqueItems, true))
  return repaired;
  const unique = MakeUnique(repaired);
  if (!(0, _index3.Check)(context, type, unique))
  throw new _error.RepairError(context, type, value, 'Failed to repair Array due to uniqueItems constraint');
  return unique;
} /* v9-cd30c57d8f860451 */
