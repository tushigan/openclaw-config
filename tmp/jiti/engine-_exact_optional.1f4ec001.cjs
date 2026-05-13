"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.InexactOptionalBuild = InexactOptionalBuild;exports.InexactOptionalCheck = InexactOptionalCheck;exports.IsExactOptional = IsExactOptional;var _index = require("../../system/settings/index.mjs");
var _index2 = require("../../guard/index.mjs");
// ------------------------------------------------------------------
// IsExactOptional
// ------------------------------------------------------------------
function IsExactOptional(required, key) {
  return required.includes(key) || _index.Settings.Get().exactOptionalPropertyTypes;
}
// ------------------------------------------------------------------
// ExactOptionalBuild
// ------------------------------------------------------------------
function InexactOptionalBuild(value, key) {
  return _index2.EmitGuard.IsUndefined(_index2.EmitGuard.Member(value, key));
}
// ------------------------------------------------------------------
// ExactOptionalCheck
// ------------------------------------------------------------------
function InexactOptionalCheck(value, key) {
  return _index2.Guard.IsUndefined(value[key]);
} /* v9-37df941298edd4b4 */
