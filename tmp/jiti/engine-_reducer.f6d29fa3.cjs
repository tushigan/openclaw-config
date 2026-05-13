"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Reducer = Reducer;
var _index = require("../../guard/index.mjs");
var _schema2 = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Reducer
//
// This function is used to generate an reducer evaluation context 
// for the allOf, anyOf, oneOf and not keywords. The reducer mechansism
// is required from 2019-09 onwards to gather evaluated keys and indices
// for the unevaluatedItems and unevaluatedProperties keywords.
//
// ------------------------------------------------------------------
//
// const context = new Context() // exterior
//
// (() => {
//   const results = []
//
//   const context_0 = context.Clone()
//   const context_1 = context.Clone()
//   const context_2 = context.Clone()
//   const context_3 = context.Clone()
//   
//   const condition_0 = ((context) => <subschema>)(context_0)
//   const condition_1 = ((context) => <subschema>)(context_1)
//   const condition_2 = ((context) => <subschema>)(context_2)
//   const condition_3 = ((context) => <subschema>)(context_3)
// 
//   if(condition_0) results.push(context_0)
//   if(condition_1) results.push(context_1)
//   if(condition_2) results.push(context_2)
//   if(condition_3) results.push(context_3)
//
//   return <check> && context.Merge(results)
// })()
//
// ------------------------------------------------------------------
function Reducer(stack, context, schemas, value, check) {
  const results = _index.EmitGuard.ConstDeclaration('results', '[]');
  const context_n = schemas.map((_schema, index) => _index.EmitGuard.ConstDeclaration(`context_${index}`, _index.EmitGuard.New('CheckContext', [])));
  const condition_n = schemas.map((schema, index) => _index.EmitGuard.ConstDeclaration(`condition_${index}`, _index.EmitGuard.Call(_index.EmitGuard.ArrowFunction(['context'], (0, _schema2.BuildSchema)(stack, context, schema, value)), [`context_${index}`])));
  const checks = schemas.map((_schema, index) => _index.EmitGuard.If(`condition_${index}`, _index.EmitGuard.Call(_index.EmitGuard.Member('results', 'push'), [`context_${index}`])));
  const returns = _index.EmitGuard.Return(_index.EmitGuard.And(check, context.Merge('results')));
  return _index.EmitGuard.Call(_index.EmitGuard.ArrowFunction([], _index.EmitGuard.Statements([results, ...context_n, ...condition_n, ...checks, returns])), []);
} /* v9-01c4d8cc48d92dda */
