"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsJsonPointer = IsJsonPointer;const JsonPointer = /^(?:\/(?:[^~/]|~0|~1)*)*$/;
/**
 * Returns true if the value is a json pointer
 * @specification
 * @source ajv-formats
 */
function IsJsonPointer(value) {
  return JsonPointer.test(value);
} /* v9-af27aa7d961a8e38 */
