"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromConstructor = FromConstructor;
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
function FromConstructor(context, type) {
  const instanceType = (0, _from_type.FromType)(context, type.instanceType);
  return class {
    constructor() {
      Object.assign(this, instanceType);
    }
  };
} /* v9-0a7722e571900e0b */
