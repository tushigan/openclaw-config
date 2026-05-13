"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.GetAdditionalProperties = GetAdditionalProperties;
var _index = require("../../guard/index.mjs"); // deno-fmt-ignore-file
function GetAdditionalProperties(type) {
  const additionalProperties = _index.Guard.HasPropertyKey(type, 'additionalProperties') ? type.additionalProperties : undefined;
  return additionalProperties;
} /* v9-9e280a1864054961 */
