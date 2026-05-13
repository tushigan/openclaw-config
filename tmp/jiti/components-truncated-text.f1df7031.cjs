"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.TruncatedText = void 0;var _utils = require("../utils.js");
/**
 * Text component that truncates to fit viewport width
 */
class TruncatedText {
  text;
  paddingX;
  paddingY;
  constructor(text, paddingX = 0, paddingY = 0) {
    this.text = text;
    this.paddingX = paddingX;
    this.paddingY = paddingY;
  }
  invalidate() {

    // No cached state to invalidate currently
  }render(width) {
    const result = [];
    // Empty line padded to width
    const emptyLine = " ".repeat(width);
    // Add vertical padding above
    for (let i = 0; i < this.paddingY; i++) {
      result.push(emptyLine);
    }
    // Calculate available width after horizontal padding
    const availableWidth = Math.max(1, width - this.paddingX * 2);
    // Take only the first line (stop at newline)
    let singleLineText = this.text;
    const newlineIndex = this.text.indexOf("\n");
    if (newlineIndex !== -1) {
      singleLineText = this.text.substring(0, newlineIndex);
    }
    // Truncate text if needed (accounting for ANSI codes)
    const displayText = (0, _utils.truncateToWidth)(singleLineText, availableWidth);
    // Add horizontal padding
    const leftPadding = " ".repeat(this.paddingX);
    const rightPadding = " ".repeat(this.paddingX);
    const lineWithPadding = leftPadding + displayText + rightPadding;
    // Pad line to exactly width characters
    const lineVisibleWidth = (0, _utils.visibleWidth)(lineWithPadding);
    const paddingNeeded = Math.max(0, width - lineVisibleWidth);
    const finalLine = lineWithPadding + " ".repeat(paddingNeeded);
    result.push(finalLine);
    // Add vertical padding below
    for (let i = 0; i < this.paddingY; i++) {
      result.push(emptyLine);
    }
    return result;
  }
}exports.TruncatedText = TruncatedText; /* v9-b9ed655cdefbc571 */
