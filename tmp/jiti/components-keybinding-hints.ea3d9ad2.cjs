"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.keyHint = keyHint;exports.keyText = keyText;exports.rawKeyHint = rawKeyHint;


var _piTui = require("@mariozechner/pi-tui");
var _theme = require("../theme/theme.js"); /**
 * Utilities for formatting keybinding hints in the UI.
 */function formatKeys(keys) {if (keys.length === 0)
  return "";
  if (keys.length === 1)
  return keys[0];
  return keys.join("/");
}
function keyText(keybinding) {
  return formatKeys((0, _piTui.getKeybindings)().getKeys(keybinding));
}
function keyHint(keybinding, description) {
  return _theme.theme.fg("dim", keyText(keybinding)) + _theme.theme.fg("muted", ` ${description}`);
}
function rawKeyHint(key, description) {
  return _theme.theme.fg("dim", key) + _theme.theme.fg("muted", ` ${description}`);
} /* v9-cb7ad3daa8ad9412 */
