"use strict";Object.defineProperty(exports, "__esModule", { value: true });exports.BranchSummaryMessageComponent = void 0;var _piTui = require("@mariozechner/pi-tui");
var _theme = require("../theme/theme.js");
var _keybindingHints = require("./keybinding-hints.js");
/**
 * Component that renders a branch summary message with collapsed/expanded state.
 * Uses same background color as custom messages for visual consistency.
 */
class BranchSummaryMessageComponent extends _piTui.Box {
  expanded = false;
  message;
  markdownTheme;
  constructor(message, markdownTheme = (0, _theme.getMarkdownTheme)()) {
    super(1, 1, (t) => _theme.theme.bg("customMessageBg", t));
    this.message = message;
    this.markdownTheme = markdownTheme;
    this.updateDisplay();
  }
  setExpanded(expanded) {
    this.expanded = expanded;
    this.updateDisplay();
  }
  invalidate() {
    super.invalidate();
    this.updateDisplay();
  }
  updateDisplay() {
    this.clear();
    const label = _theme.theme.fg("customMessageLabel", `\x1b[1m[branch]\x1b[22m`);
    this.addChild(new _piTui.Text(label, 0, 0));
    this.addChild(new _piTui.Spacer(1));
    if (this.expanded) {
      const header = "**Branch Summary**\n\n";
      this.addChild(new _piTui.Markdown(header + this.message.summary, 0, 0, this.markdownTheme, {
        color: (text) => _theme.theme.fg("customMessageText", text)
      }));
    } else
    {
      this.addChild(new _piTui.Text(_theme.theme.fg("customMessageText", "Branch summary (") +
      _theme.theme.fg("dim", (0, _keybindingHints.keyText)("app.tools.expand")) +
      _theme.theme.fg("customMessageText", " to expand)"), 0, 0));
    }
  }
}exports.BranchSummaryMessageComponent = BranchSummaryMessageComponent; /* v9-3bd4a296a58e8d6c */
