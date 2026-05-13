"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.IsIri = IsIri; /**
 * Returns true if the value is a Iri
 * @specification
 */
function IsIri(value) {
  try {
    new URL(value);
    return true;
  }
  catch {
    return false;
  }
} /* v9-8f4391527d12f971 */
