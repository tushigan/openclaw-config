"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsUuid = IsUuid;const Uuid = /^(?:urn:uuid:)?[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i;
/**
 * Returns true if the value is a uuid
 * @specification
 * @source ajv-formats
 */
function IsUuid(value) {
  return Uuid.test(value);
} /* v9-2f64589051dad005 */
