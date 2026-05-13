"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsRegex = IsRegex; /**
 * Returns true if the value is a regular expression string pattern
 * @specification
 * @source ajv-formats
 */
function IsRegex(value) {
  if (value.length === 0) {
    return false;
  }
  try {
    new RegExp(value);
    return true;
  }
  catch {
    return false;
  }
} /* v9-0a5b05d8e4b35689 */
