"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsEmail = IsEmail;const Email = /^(?!.*\.\.)[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*$/i;
/**
 * Returns true if the value is an Email
 * @specification ajv-formats
 */
function IsEmail(value) {
  return Email.test(value);
} /* v9-116f5e0ff31b443e */
