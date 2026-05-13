"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.selectSession = selectSession;


var _piTui = require("@mariozechner/pi-tui");
var _keybindings = require("../core/keybindings.js");
var _sessionSelector = require("../modes/interactive/components/session-selector.js"); /**
 * TUI session selector for --resume flag
 */ /** Show TUI session selector and return selected session path or null if cancelled */async function selectSession(currentSessionsLoader, allSessionsLoader) {
  return new Promise((resolve) => {
    const ui = new _piTui.TUI(new _piTui.ProcessTerminal());
    const keybindings = _keybindings.KeybindingsManager.create();
    (0, _piTui.setKeybindings)(keybindings);
    let resolved = false;
    const selector = new _sessionSelector.SessionSelectorComponent(currentSessionsLoader, allSessionsLoader, (path) => {
      if (!resolved) {
        resolved = true;
        ui.stop();
        resolve(path);
      }
    }, () => {
      if (!resolved) {
        resolved = true;
        ui.stop();
        resolve(null);
      }
    }, () => {
      ui.stop();
      process.exit(0);
    }, () => ui.requestRender(), { showRenameHint: false, keybindings });
    ui.addChild(selector);
    ui.setFocus(selector.getSessionList());
    ui.start();
  });
} /* v9-2af8b98aca1c060c */
