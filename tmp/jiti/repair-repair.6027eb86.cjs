"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Repair = Repair;
var _index = require("../../system/arguments/index.mjs");
var _from_type = require("./from_type.mjs");
var _index2 = require("../assert/index.mjs"); // deno-fmt-ignore-file
/**
 * Repairs a value to match the provided type. This function is intended for data migration
 * scenarios where existing values need to be migrating to an updated type. This function will
 * repair partially mismatched values by populating missing sub-properties and elements with
 * default structures derived from the type. If the value already conforms to the type, no
 * action is performed.
 */
function Repair(...args) {
  const [context, type, value] = _index.Arguments.Match(args, {
    3: (context, type, value) => [context, type, value],
    2: (type, value) => [{}, type, value]
  });
  const repaired = (0, _from_type.FromType)(context, type, value);
  (0, _index2.Assert)(context, type, repaired);
  return repaired;
} /* v9-67d3b51dcaa01e4e */
