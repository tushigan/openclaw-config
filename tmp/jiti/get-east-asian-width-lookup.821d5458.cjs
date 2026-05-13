"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.getCategory = getCategory;exports.isWide = exports.isFullWidth = exports.isAmbiguous = void 0;var _lookupData = require("./lookup-data.js");




















var _utilities = require("./utilities.js");

const commonCjkCodePoint = 0x4E_00;
const [wideFastPathStart, wideFastPathEnd] = /* #__PURE__ */findWideFastPathRange(_lookupData.wideRanges);

// Use a hot-path range so common `isWide` calls can skip binary search.
// The range containing U+4E00 covers common CJK ideographs;
// fallback to the largest range for resilience to Unicode table changes.
function findWideFastPathRange(ranges) {
  let fastPathStart = ranges[0];
  let fastPathEnd = ranges[1];

  for (let index = 0; index < ranges.length; index += 2) {
    const start = ranges[index];
    const end = ranges[index + 1];

    if (
    commonCjkCodePoint >= start &&
    commonCjkCodePoint <= end)
    {
      return [start, end];
    }

    if (end - start > fastPathEnd - fastPathStart) {
      fastPathStart = start;
      fastPathEnd = end;
    }
  }

  return [fastPathStart, fastPathEnd];
}

const isAmbiguous = (codePoint) => {
  if (
  codePoint < _lookupData.ambiguousMinimalCodePoint ||
  codePoint > _lookupData.ambiguousMaximumCodePoint)
  {
    return false;
  }

  return (0, _utilities.isInRange)(_lookupData.ambiguousRanges, codePoint);
};exports.isAmbiguous = isAmbiguous;

const isFullWidth = (codePoint) => {
  if (
  codePoint < _lookupData.fullwidthMinimalCodePoint ||
  codePoint > _lookupData.fullwidthMaximumCodePoint)
  {
    return false;
  }

  return (0, _utilities.isInRange)(_lookupData.fullwidthRanges, codePoint);
};exports.isFullWidth = isFullWidth;

const isHalfWidth = (codePoint) => {
  if (
  codePoint < _lookupData.halfwidthMinimalCodePoint ||
  codePoint > _lookupData.halfwidthMaximumCodePoint)
  {
    return false;
  }

  return (0, _utilities.isInRange)(_lookupData.halfwidthRanges, codePoint);
};

const isNarrow = (codePoint) => {
  if (
  codePoint < _lookupData.narrowMinimalCodePoint ||
  codePoint > _lookupData.narrowMaximumCodePoint)
  {
    return false;
  }

  return (0, _utilities.isInRange)(_lookupData.narrowRanges, codePoint);
};

const isWide = (codePoint) => {
  if (
  codePoint >= wideFastPathStart &&
  codePoint <= wideFastPathEnd)
  {
    return true;
  }

  if (
  codePoint < _lookupData.wideMinimalCodePoint ||
  codePoint > _lookupData.wideMaximumCodePoint)
  {
    return false;
  }

  return (0, _utilities.isInRange)(_lookupData.wideRanges, codePoint);
};exports.isWide = isWide;

function getCategory(codePoint) {
  if (isAmbiguous(codePoint)) {
    return 'ambiguous';
  }

  if (isFullWidth(codePoint)) {
    return 'fullwidth';
  }

  if (isHalfWidth(codePoint)) {
    return 'halfwidth';
  }

  if (isNarrow(codePoint)) {
    return 'narrow';
  }

  if (isWide(codePoint)) {
    return 'wide';
  }

  return 'neutral';
} /* v9-9034e0e4b661b6b7 */
