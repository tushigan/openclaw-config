"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.UnionScoreSelect = UnionScoreSelect;
var _index = require("../../type/index.mjs");
var _index2 = require("../../guard/index.mjs");
var _index3 = require("../check/index.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Deref
// ------------------------------------------------------------------
function Deref(context, type, value) {
  return (0, _index.IsRef)(type) ?
  _index2.Guard.HasPropertyKey(context, type.$ref) ?
  Deref(context, context[type.$ref], value) :
  (() => {throw new Error('Unable to Deref target');})() :
  type;
}
// ------------------------------------------------------------------
// The following will score a schema against a value. For objects,
// the score is the tally of points awarded for each property of
// the value. Property points are (1.0 / propertyCount) to prevent
// large property counts biasing results. Properties that match
// literal values are maximally awarded as literals are typically
// used as union discriminator fields.
// ------------------------------------------------------------------
function ScoreVariant(context, type, value) {
  // scoring is only possible for object types.
  if (!((0, _index.IsObject)(type) && _index2.Guard.IsObject(value)))
  return 0;
  const keys = _index2.Guard.Keys(value);
  const entries = _index2.Guard.Entries(type.properties);
  return entries.reduce((result, [key, schema]) => {
    const literal = (0, _index.IsLiteral)(schema) && _index2.Guard.IsEqual(schema.const, value[key]) ? 100 : 0;
    const checks = (0, _index3.Check)(context, schema, value[key]) ? 10 : 0;
    const exists = keys.includes(key) ? 1 : 0;
    return result + (literal + checks + exists);
  }, 0);
}
// ------------------------------------------------------------------
// UnionScoreSelect
// ------------------------------------------------------------------
/** Scores Union variants and returns the best match for the given value */
function UnionScoreSelect(context, type, value) {
  const schemas = type.anyOf.map((schema) => Deref(context, schema, value));
  let [select, best] = [schemas[0], 0];
  for (const schema of schemas) {
    const score = ScoreVariant(context, schema, value);
    if (score > best) {
      select = schema;
      best = score;
    }
  }
  return select;
} /* v9-d1417f77d669eb26 */
