"use strict";Object.defineProperty(exports, "__esModule", { value: true });Object.defineProperty(exports, "_isFullWidth", { enumerable: true, get: function () {return _lookup.isFullWidth;} });Object.defineProperty(exports, "_isWide", { enumerable: true, get: function () {return _lookup.isWide;} });exports.eastAsianWidth = eastAsianWidth;exports.eastAsianWidthType = eastAsianWidthType;var _lookup = require("./lookup.js");

function validate(codePoint) {
  if (!Number.isSafeInteger(codePoint)) {
    throw new TypeError(`Expected a code point, got \`${typeof codePoint}\`.`);
  }
}

function eastAsianWidthType(codePoint) {
  validate(codePoint);

  return (0, _lookup.getCategory)(codePoint);
}

function eastAsianWidth(codePoint, { ambiguousAsWide = false } = {}) {
  validate(codePoint);

  if (
  (0, _lookup.isFullWidth)(codePoint) ||
  (0, _lookup.isWide)(codePoint) ||
  ambiguousAsWide && (0, _lookup.isAmbiguous)(codePoint))
  {
    return 2;
  }

  return 1;
}

// Private exports for https://github.com/sindresorhus/is-fullwidth-code-point /* v9-8479e19cc8d10860 */
