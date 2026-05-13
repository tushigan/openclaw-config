"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildDependentRequired = BuildDependentRequired;exports.CheckDependentRequired = CheckDependentRequired;exports.ErrorDependentRequired = ErrorDependentRequired;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildDependentRequired(_stack, _context, schema, value) {
  const isLength = _index.EmitGuard.IsEqual(_index.EmitGuard.Member(_index.EmitGuard.Keys(value), 'length'), _index.EmitGuard.Constant(0));
  const isEvery = _index.EmitGuard.ReduceAnd(_index.Guard.Entries(schema.dependentRequired).map(([key, keys]) => {
    const notKey = _index.EmitGuard.Not(_index.EmitGuard.HasPropertyKey(value, _index.EmitGuard.Constant(key)));
    const everyKey = _index.EmitGuard.ReduceAnd(keys.map((key) => _index.EmitGuard.HasPropertyKey(value, _index.EmitGuard.Constant(key))));
    return _index.EmitGuard.Or(notKey, everyKey);
  }));
  return _index.EmitGuard.Or(isLength, isEvery);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckDependentRequired(_stack, _context, schema, value) {
  const isLength = _index.Guard.IsEqual(_index.Guard.Keys(value).length, 0);
  const isEvery = _index.Guard.Every(_index.Guard.Entries(schema.dependentRequired), 0, ([key, keys]) => {
    return !_index.Guard.HasPropertyKey(value, key) ||
    keys.every((key) => _index.Guard.HasPropertyKey(value, key));
  });
  return isLength || isEvery;
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorDependentRequired(_stack, context, schemaPath, instancePath, schema, value) {
  const isLength = _index.Guard.IsEqual(_index.Guard.Keys(value).length, 0);
  const isEveryEntry = _index.Guard.EveryAll(_index.Guard.Entries(schema.dependentRequired), 0, ([key, keys]) => {
    return !_index.Guard.HasPropertyKey(value, key) || _index.Guard.EveryAll(keys, 0, (dependency) => _index.Guard.HasPropertyKey(value, dependency) || context.AddError({
      keyword: 'dependentRequired',
      schemaPath,
      instancePath,
      params: { property: key, dependencies: keys }
    }));
  });
  return isLength || isEveryEntry;
} /* v9-885c33d8046d2361 */
