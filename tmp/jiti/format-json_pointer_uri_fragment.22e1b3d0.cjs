"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsJsonPointerUriFragment = IsJsonPointerUriFragment;const JsonPointerUriFragment = /^#(?:\/(?:[a-z0-9_\-.!$&'()*+,;:=@]|%[0-9a-f]{2}|~0|~1)*)*$/i;
/**
 * Returns true if the value is a json pointer uri fragment
 * @specification
 * @source ajv-formats
 */
function IsJsonPointerUriFragment(value) {
  return JsonPointerUriFragment.test(value);
} /* v9-a43e381d02fe0596 */
