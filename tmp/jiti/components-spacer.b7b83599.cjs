"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.Spacer = void 0; /**
 * Spacer component that renders empty lines
 */
class Spacer {
  lines;
  constructor(lines = 1) {
    this.lines = lines;
  }
  setLines(lines) {
    this.lines = lines;
  }
  invalidate() {

    // No cached state to invalidate currently
  }render(_width) {
    const result = [];
    for (let i = 0; i < this.lines; i++) {
      result.push("");
    }
    return result;
  }
}exports.Spacer = Spacer; /* v9-752d3dcdddcac44c */
