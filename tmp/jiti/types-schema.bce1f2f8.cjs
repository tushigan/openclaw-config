"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsBooleanSchema = IsBooleanSchema;exports.IsSchema = IsSchema;exports.IsSchemaObject = IsSchemaObject;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
/** Returns true if this value is object like */
function IsSchemaObject(value) {
  return _index.Guard.IsObject(value) && !_index.Guard.IsArray(value);
}
/** Returns true if this value is a boolean */
function IsBooleanSchema(value) {
  return _index.Guard.IsBoolean(value);
}
/** Returns true if this value is schema like */
function IsSchema(value) {
  return IsSchemaObject(value) || IsBooleanSchema(value);
} /* v9-0154feec8cf3c50c */
