"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsIdnEmail = IsIdnEmail;const IdnEmail = /^(?!.*\.\.)[\p{L}\p{N}!#$%&'*+/=?^_`{|}~-]+(?:\.[\p{L}\p{N}!#$%&'*+/=?^_`{|}~-]+)*@[\p{L}\p{N}](?:[\p{L}\p{N}-]{0,61}[\p{L}\p{N}])?(?:\.[\p{L}\p{N}](?:[\p{L}\p{N}-]{0,61}[\p{L}\p{N}])?)*$/iu;
/**
 * Returns true if the value is an IdnEmail
 * @specification ajv-formats (unicode-extension)
 */
function IsIdnEmail(value) {
  return IdnEmail.test(value);
} /* v9-823ae650ee2908ee */
