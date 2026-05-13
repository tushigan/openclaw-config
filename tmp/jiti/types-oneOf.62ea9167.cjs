"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsOneOf = IsOneOf;
var _index = require("../../guard/index.mjs");
var _schema = require("./schema.mjs"); // deno-fmt-ignore-file
// ------------------------------------------------------------------
// Guard
// ------------------------------------------------------------------
/**
 * Returns true if the schema contains a valid oneOf property
 * @specification Json Schema 7
 */
function IsOneOf(schema) {
  return _index.Guard.HasPropertyKey(schema, 'oneOf') &&
  _index.Guard.IsArray(schema.oneOf) &&
  schema.oneOf.every((value) => (0, _schema.IsSchema)(value));
} /* v9-31ff32dd2f792f5d */
