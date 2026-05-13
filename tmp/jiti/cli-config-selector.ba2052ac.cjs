"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.selectConfig = selectConfig;


var _piTui = require("@mariozechner/pi-tui");
var _configSelector = require("../modes/interactive/components/config-selector.js");
var _theme = require("../modes/interactive/theme/theme.js"); /**
 * TUI config selector for `pi config` command
 */ /** Show TUI config selector and return when closed */async function selectConfig(options) {
  // Initialize theme before showing TUI
  (0, _theme.initTheme)(options.settingsManager.getTheme(), true);
  return new Promise((resolve) => {
    const ui = new _piTui.TUI(new _piTui.ProcessTerminal());
    let resolved = false;
    const selector = new _configSelector.ConfigSelectorComponent(options.resolvedPaths, options.settingsManager, options.cwd, options.agentDir, () => {
      if (!resolved) {
        resolved = true;
        ui.stop();
        (0, _theme.stopThemeWatcher)();
        resolve();
      }
    }, () => {
      ui.stop();
      (0, _theme.stopThemeWatcher)();
      process.exit(0);
    }, () => ui.requestRender());
    ui.addChild(selector);
    ui.setFocus(selector.getResourceList());
    ui.start();
  });
} /* v9-dbb7674c98a2e911 */
