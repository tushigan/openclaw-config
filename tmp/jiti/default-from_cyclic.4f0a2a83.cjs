"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.FromCyclic = FromCyclic;

var _index = require("../../type/index.mjs");
var _from_type = require("./from_type.mjs"); // deno-fmt-ignore-file
// deno-lint-ignore-file
function FromCyclic(context, type, value) {return (0, _from_type.FromType)({ ...context, ...type.$defs }, (0, _index.Ref)(type.$ref), value);
} /* v9-a97edd89fe63b4b8 */
