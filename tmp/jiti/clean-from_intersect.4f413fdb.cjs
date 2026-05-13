"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromIntersect = FromIntersect;
var _index = require("../../type/index.mjs");
var _index2 = require("../../guard/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// EvaluateIntersection
// ------------------------------------------------------------------
function EvaluateIntersection(context, type) {
  // Note: reinterpret unevaluatedProperties as additionalProperties
  const additionalProperties = _index2.Guard.HasPropertyKey(type, 'unevaluatedProperties') ?
  { additionalProperties: type.unevaluatedProperties } :
  {};
  const instantiated = (0, _index.Instantiate)(context, type);
  const evaluated = (0, _index.Evaluate)(instantiated);
  return (0, _index.IsObject)(evaluated) ?
  (0, _index.Options)(evaluated, additionalProperties) :
  evaluated;
}
// ------------------------------------------------------------------
// FromIntersection
// ------------------------------------------------------------------
function FromIntersect(context, type, value) {
  // Note: Evaluate and route back to FromType in evaluated form (likely an Object)
  const evaluated = EvaluateIntersection(context, type);
  return (0, _from_type.FromType)(context, evaluated, value);
} /* v9-6e462fc5e9556577 */
