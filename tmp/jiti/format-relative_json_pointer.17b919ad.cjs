"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsRelativeJsonPointer = IsRelativeJsonPointer;const RelativeJsonPointer = /^(?:0|[1-9][0-9]*)(?:#|(?:\/(?:[^~/]|~0|~1)*)*)$/;
/**
 * Returns true if the value is a relative json pointer
 * @specification
 * @source ajv-formats
 */
function IsRelativeJsonPointer(value) {
  return RelativeJsonPointer.test(value);
} /* v9-b326f65e5db44a2b */
