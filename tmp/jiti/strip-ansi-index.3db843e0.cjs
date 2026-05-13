"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.default = stripAnsi;var _ansiRegex = _interopRequireDefault(require("ansi-regex"));function _interopRequireDefault(e) {return e && e.__esModule ? e : { default: e };}

const regex = (0, _ansiRegex.default)();

function stripAnsi(string) {
  if (typeof string !== 'string') {
    throw new TypeError(`Expected a \`string\`, got \`${typeof string}\``);
  }

  // Fast path: ANSI codes require ESC (7-bit) or CSI (8-bit) introducer
  if (!string.includes('\u001B') && !string.includes('\u009B')) {
    return string;
  }

  // Even though the regex is global, we don't need to reset the `.lastIndex`
  // because unlike `.exec()` and `.test()`, `.replace()` does it automatically
  // and doing it manually has a performance penalty.
  return string.replace(regex, '');
} /* v9-62cae56d45f22c79 */
