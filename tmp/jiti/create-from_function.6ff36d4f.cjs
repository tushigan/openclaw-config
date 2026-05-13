"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromFunction = FromFunction;
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromFunction(context, type) {
  const returnType = (0, _from_type.FromType)(context, type.returnType);
  return () => returnType;
} /* v9-fe98629dbc54250e */
