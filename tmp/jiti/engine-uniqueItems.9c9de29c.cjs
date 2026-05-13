"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildUniqueItems = BuildUniqueItems;exports.CheckUniqueItems = CheckUniqueItems;exports.ErrorUniqueItems = ErrorUniqueItems;
var _index = require("../../system/hashing/index.mjs");
var _index2 = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Valid
// ------------------------------------------------------------------
function IsValid(schema) {
  return !_index2.Guard.IsEqual(schema.uniqueItems, false);
}
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildUniqueItems(_stack, _context, schema, value) {
  if (!IsValid(schema))
  return _index2.EmitGuard.Constant(true);
  const set = _index2.EmitGuard.Member(_index2.EmitGuard.New('Set', [_index2.EmitGuard.Call(_index2.EmitGuard.Member(value, 'map'), [_index2.EmitGuard.Member('Hashing', 'Hash')])]), 'size');
  const isLength = _index2.EmitGuard.Member(value, 'length');
  return _index2.EmitGuard.IsEqual(set, isLength);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckUniqueItems(_stack, _context, schema, value) {
  if (!IsValid(schema))
  return true;
  const set = new Set(value.map(_index.Hashing.Hash)).size;
  const isLength = value.length;
  return _index2.Guard.IsEqual(set, isLength);
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorUniqueItems(_stack, context, schemaPath, instancePath, schema, value) {
  if (!IsValid(schema))
  return true;
  const set = new Set();
  const duplicateItems = value.reduce((result, value, index) => {
    const hash = _index.Hashing.Hash(value);
    if (set.has(hash))
    return [...result, index];
    set.add(hash);
    return result;
  }, []);
  const isUniqueItems = _index2.Guard.IsEqual(duplicateItems.length, 0);
  return isUniqueItems || context.AddError({
    keyword: 'uniqueItems',
    schemaPath,
    instancePath,
    params: { duplicateItems }
  });
} /* v9-f0f4cf04b2c4c225 */
