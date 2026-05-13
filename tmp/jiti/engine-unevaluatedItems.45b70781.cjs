"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BuildUnevaluatedItems = BuildUnevaluatedItems;exports.CheckUnevaluatedItems = CheckUnevaluatedItems;exports.ErrorUnevaluatedItems = ErrorUnevaluatedItems;
var _unique = require("./_unique.mjs");
var _context = require("./_context.mjs");
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Build
// ------------------------------------------------------------------
function BuildUnevaluatedItems(stack, context, schema, value) {
  const [index, item] = [(0, _unique.Unique)(), (0, _unique.Unique)()];
  const indices = _index.EmitGuard.Call(_index.EmitGuard.Member('context', 'GetIndices'), []);
  const hasIndex = _index.EmitGuard.Call(_index.EmitGuard.Member('indices', 'has'), [index]);
  const isSchema = (0, _schema.BuildSchema)(stack, context, schema.unevaluatedItems, item);
  const addIndex = _index.EmitGuard.Call(_index.EmitGuard.Member('context', 'AddIndex'), [index]);
  const isEvery = _index.EmitGuard.Every(value, _index.EmitGuard.Constant(0), [item, index], _index.EmitGuard.And(_index.EmitGuard.Or(hasIndex, isSchema), addIndex));
  return _index.EmitGuard.Call(_index.EmitGuard.ArrowFunction(['context'], _index.EmitGuard.Statements([
  _index.EmitGuard.ConstDeclaration('indices', indices),
  _index.EmitGuard.Return(isEvery)]
  )), ['context']);
}
// ------------------------------------------------------------------
// Check
// ------------------------------------------------------------------
function CheckUnevaluatedItems(stack, context, schema, value) {
  const indices = context.GetIndices();
  return _index.Guard.Every(value, 0, (item, index) => {
    return (indices.has(index) || (0, _schema.CheckSchema)(stack, context, schema.unevaluatedItems, item)) &&
    context.AddIndex(index);
  });
}
// ------------------------------------------------------------------
// Error
// ------------------------------------------------------------------
function ErrorUnevaluatedItems(stack, context, schemaPath, instancePath, schema, value) {
  const indices = context.GetIndices();
  const unevaluatedItems = [];
  const isUnevaluatedItems = _index.Guard.EveryAll(value, 0, (item, index) => {
    const nextContext = new _context.AccumulatedErrorContext();
    const isEvaluatedItem = (indices.has(index) || (0, _schema.ErrorSchema)(stack, nextContext, schemaPath, instancePath, schema.unevaluatedItems, item)) &&
    context.AddIndex(index);
    if (!isEvaluatedItem)
    unevaluatedItems.push(index);
    return isEvaluatedItem;
  });
  return isUnevaluatedItems || context.AddError({
    keyword: 'unevaluatedItems',
    schemaPath,
    instancePath,
    params: { unevaluatedItems }
  });
} /* v9-e9f6bae61003b0c5 */
