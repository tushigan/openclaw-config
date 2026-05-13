"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsUriTemplate = IsUriTemplate; // deno-lint-ignore-file
const UriTemplate = /^(?:(?:[^\x00-\x20"'<>%\\^`{|}]|%[0-9a-f]{2})|\{[+#./;?&=,!@|]?(?:[a-z0-9_]|%[0-9a-f]{2})+(?::[1-9][0-9]{0,3}|\*)?(?:,(?:[a-z0-9_]|%[0-9a-f]{2})+(?::[1-9][0-9]{0,3}|\*)?)*\})*$/i;
/**
 * Returns true if the value is a uri template
 * @specification
 * @source ajv-formats
 */
function IsUriTemplate(value) {
  return UriTemplate.test(value);
} /* v9-dc9efb6db2033acd */
